from __future__ import annotations

import typing
from collections import deque
from typing import Any

import pyarrow
import pyarrow.parquet

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..convert.batch import BatchSelection, chunk_rows, resolve_row_window, select_rows, to_pyarrow_expression
from ..exceptions import FormatParseError, WriteError
from ..helpers.utils import normalize_extended_json
from ..types import Row

DEFAULT_BATCH_SIZE = 1024


def _has_nested_types(schema: pyarrow.Schema) -> bool:
    return any(pyarrow.types.is_nested(field.type) for field in schema)


def fields_to_pyarrow_schema(keys):
    fields = []
    for key in keys:
        fields.append((key, pyarrow.string()))
    return pyarrow.schema(fields)


class ParquetIterable(BaseFileIterable):
    datamode = "binary"
    supports_native_batch = True
    supports_arrow_batches = True

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        mode: str = "r",
        codec: BaseCodec | None = None,
        keys: list[str] | None = None,
        schema: list[str] = None,
        compression: str = "snappy",
        adapt_schema: bool = True,
        use_pandas: bool = True,
        batch_size: int = DEFAULT_BATCH_SIZE,
        row_group_size: int | None = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        self.use_pandas = use_pandas
        self.__buffer = []
        # Batches converted to Arrow once the writer schema is known, flushed per row group.
        self.__tables: list[pyarrow.Table] = []
        self.__buffered_rows = 0
        self.adapt_schema = adapt_schema
        self.keys = keys
        self.schema = schema
        self.compression = compression
        self.batch_size = batch_size
        # Read batch size and write row-group size are independent concerns.
        # Keeping a bounded row-group target avoids creating one row group per
        # call to ``write`` while still allowing readers to choose a small
        # memory footprint.
        self.row_group_size = row_group_size or batch_size
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, options=options)
        self.reset()
        self.is_data_written = False
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        self.reader = None
        if self.mode == "r":
            try:
                self.reader = pyarrow.parquet.ParquetFile(self.fobj)
            except (pyarrow.ArrowInvalid, OSError, ValueError) as e:
                raise FormatParseError(
                    format_id="parquet",
                    message=str(e),
                    filename=getattr(self, "filename", None),
                ) from e
            self._batch_iterator = self.reader.iter_batches(batch_size=self.batch_size)
            self._pending_rows = deque()
        #           self.tbl = self.reader.to_table()
        self.writer = None
        if self.mode == "w":
            # Reset write state for streaming writes
            self.__buffer = []
            self.__tables = []
            self.__buffered_rows = 0
            self.is_data_written = False
            if not self.adapt_schema:
                if self.schema is not None:
                    struct_schema = self.schema
                else:
                    struct_schema = fields_to_pyarrow_schema(self.keys)
                self.writer = pyarrow.parquet.ParquetWriter(
                    self.fobj, struct_schema, compression=self.compression, use_dictionary=False
                )
                self.is_data_written = True

    #            self.writer = pyorc.Writer(
    #                self.fobj, "struct<%s>" % (','.join(struct_schema)),
    #                struct_repr=pyorc.StructRepr.DICT,
    #                compression=self.compression, compression_strategy=1
    #            )

    @staticmethod
    def id() -> str:
        return "parquet"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def is_streaming(self) -> bool:
        """Returns True - Parquet streams row groups"""
        return True

    def totals(self):
        """Returns file totals"""
        if self.reader is None:
            return 0
        try:
            meta = self.reader.metadata
            return meta.num_rows if meta is not None else 0
        except Exception:
            return self.reader.scan_contents()

    def _normalize_records_to_schema(self, records: list[Row], schema: pyarrow.Schema) -> list[dict]:
        """Normalize records to match an existing schema field order and names."""
        field_names = [field.name for field in schema]
        return [{field_name: record.get(field_name) for field_name in field_names} for record in records]

    def _prepare_records(self, records: list[Row]) -> list[Row]:
        """Normalize record values before PyArrow schema inference."""
        return [normalize_extended_json(record) for record in records]

    def _to_arrow(self, records: list[Row], schema: pyarrow.Schema | None = None) -> pyarrow.Table:
        """Convert records to Arrow once; unwrap extended JSON only when the batch needs it.

        ``Table.from_pylist`` takes the columns from ``schema`` (missing keys become nulls,
        unknown keys are dropped) or, without a schema, from the first record. A flat result
        means the batch had no dict or list values, so ``normalize_extended_json`` would not
        have changed it; otherwise the batch is normalized and converted again.
        """
        if schema is None or not _has_nested_types(schema):
            try:
                table = pyarrow.Table.from_pylist(records, schema=schema)
            except (pyarrow.ArrowException, TypeError, ValueError):
                table = None
            if table is not None and not _has_nested_types(table.schema):
                return table
        return pyarrow.Table.from_pylist(self._prepare_records(records), schema=schema)

    def _write_records(self, records: list[Row]) -> None:
        """Write records to Parquet, aligning schema when appending to an existing file."""
        if self.writer is None:
            table = self._to_arrow(records)
            self.writer = pyarrow.parquet.ParquetWriter(
                self.fobj, table.schema, compression=self.compression, use_dictionary=False
            )
        else:
            table = self._to_arrow(records, self.writer.schema)
        self.writer.write_table(table)

    def flush(self):
        """Flush all data"""
        if self.__buffer:
            self._write_records(self.__buffer)
            self.__buffer = []
        writer = self.writer
        # Arrow tables are only buffered once the writer (and its schema) exists.
        if self.__tables and writer is not None:
            tables, self.__tables, self.__buffered_rows = self.__tables, [], 0
            writer.write_table(tables[0] if len(tables) == 1 else pyarrow.concat_tables(tables))

    def close(self):
        """Close iterable"""
        if self.mode == "w":
            self.flush()
        if self.writer is not None:
            self.writer.close()
        super().close()

    def _fill_pending_rows(self) -> bool:
        """Load one Arrow batch into the shared row cursor."""
        if self._pending_rows:
            return True
        try:
            self._pending_rows.extend(next(self._batch_iterator).to_pylist())
        except StopIteration:
            return False
        return bool(self._pending_rows)

    def read(self, skip_empty: bool = True) -> dict:
        """Read single record"""
        if not self._fill_pending_rows():
            raise StopIteration
        row = self._pending_rows.popleft()
        self.pos += 1
        return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk Parquet records efficiently using batch reading.

        This optimized implementation directly consumes batches from iter_batches()
        instead of calling read() in a loop, providing significant performance
        improvements for columnar data access.
        """
        chunk = []
        while len(chunk) < num and self._fill_pending_rows():
            take = min(num - len(chunk), len(self._pending_rows))
            for _ in range(take):
                chunk.append(self._pending_rows.popleft())
            self.pos += take

        return chunk

    def read_batches(self, selection: BatchSelection | None = None):
        """Yield scanner batches with projection/filter pushdown.

        Column projection is pushed to the Parquet scanner. Structured
        predicates are pushed through ``pyarrow.dataset`` when the source is
        a plain file path; otherwise :exc:`NotImplementedError` triggers the
        documented row fallback (which applies the predicate row-wise).
        Row windows and slice steps are applied with the shared selection
        semantics after any pushed operations.
        """
        selection = selection or BatchSelection()
        if selection.table is not None:
            raise NotImplementedError("Parquet native batches support columns, predicates and row ranges, not tables")
        start, stop, step = resolve_row_window(selection)
        target = selection.batch_size or self.batch_size
        window = BatchSelection(row_range=(start, stop) if start or stop is not None else None)
        if step != 1:
            window = BatchSelection(slice=(start, stop, step))

        if selection.predicate is not None:
            if not self.filename:
                raise NotImplementedError("Parquet predicate pushdown requires a file path source")
            import pyarrow.dataset as ds

            dataset = ds.dataset(self.filename, format="parquet")
            scanner = dataset.scanner(
                columns=list(selection.columns) if selection.columns is not None else None,
                filter=to_pyarrow_expression(selection.predicate),
                batch_size=target,
                # Deterministic fragment/row-group order keeps results
                # identical to the sequential row path.
                use_threads=False,
            )

            def filtered_rows():
                for batch in scanner.to_batches():
                    yield from batch.to_pylist()

            for chunk in chunk_rows(select_rows(filtered_rows(), window), target):
                self.pos += len(chunk)
                yield chunk
            return

        if selection.columns is not None:
            if self.pos != 0 or self._pending_rows:
                raise NotImplementedError("Parquet projection pushdown requires a fresh reader")
            self._batch_iterator = self.reader.iter_batches(
                batch_size=target,
                columns=list(selection.columns),
            )

        def rows():
            for batch in self._batch_iterator:
                yield from batch.to_pylist()

        for chunk in chunk_rows(select_rows(rows(), window), target):
            self.pos += len(chunk)
            yield chunk

    def write(self, record: Row) -> None:
        """Write single record"""
        if self._validation_hooks:
            validated = self._apply_validation_hooks(record)
            if validated is None:
                return
            record = validated
        self.write_bulk(
            [
                record,
            ]
        )

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk records"""
        if self._validation_hooks:
            validated_records = []
            for record in records:
                validated = self._apply_validation_hooks(record)
                if validated is not None:
                    validated_records.append(validated)
            records = validated_records
        if not records:
            return

        if self.writer is None:
            # The schema is inferred from the first row group at the first flush.
            self.__buffer.extend(records)
            if len(self.__buffer) >= self.row_group_size:
                self.flush()
            return

        # Convert against the established schema once: alignment errors surface at the
        # offending batch, and the converted batch is what gets written.
        try:
            table = self._to_arrow(records, self.writer.schema)
        except Exception as exc:
            raise WriteError(
                f"Failed to write records aligned to the existing Parquet schema ({self.writer.schema.names}): {exc}",
                filename=getattr(self, "filename", None),
                error_code="SCHEMA_ALIGNMENT_FAILED",
            ) from exc
        # Buffer to a bounded row group rather than one physical row group per call.
        self.__tables.append(table)
        self.__buffered_rows += table.num_rows
        if self.__buffered_rows >= self.row_group_size:
            self.flush()

    def write_batch(self, records: list[Row]) -> None:
        """Native batch writer hook used by columnar conversion."""
        self.write_bulk(records)

    def write_arrow_batch(self, batch: Any) -> None:
        """Native Arrow hook: buffer a ``RecordBatch`` or ``Table`` without building rows."""
        table = batch if isinstance(batch, pyarrow.Table) else pyarrow.Table.from_batches([batch])
        if self.__buffer:
            self.flush()
        if self.writer is None:
            self.writer = pyarrow.parquet.ParquetWriter(
                self.fobj, table.schema, compression=self.compression, use_dictionary=False
            )
        elif table.schema != self.writer.schema:
            try:
                table = table.select(self.writer.schema.names).cast(self.writer.schema)
            except (pyarrow.ArrowException, KeyError, ValueError) as exc:
                raise WriteError(
                    f"Failed to align an Arrow batch to the Parquet schema ({self.writer.schema.names}): {exc}",
                    filename=getattr(self, "filename", None),
                    error_code="SCHEMA_ALIGNMENT_FAILED",
                ) from exc
        self.__tables.append(table)
        self.__buffered_rows += table.num_rows
        if self.__buffered_rows >= self.row_group_size:
            self.flush()
