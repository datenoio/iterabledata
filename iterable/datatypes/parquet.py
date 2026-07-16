from __future__ import annotations

import typing
from collections import deque
from typing import Any

import pyarrow
import pyarrow.parquet

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..convert.batch import BatchSelection
from ..exceptions import FormatParseError, WriteError
from ..helpers.utils import normalize_extended_json
from ..types import Row

DEFAULT_BATCH_SIZE = 1024


def fields_to_pyarrow_schema(keys):
    fields = []
    for key in keys:
        fields.append((key, pyarrow.string()))
    return pyarrow.schema(fields)


class ParquetIterable(BaseFileIterable):
    datamode = "binary"
    supports_native_batch = True

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

    def _write_records(self, records: list[Row]) -> None:
        """Write records to Parquet, aligning schema when appending to an existing file."""
        records = self._prepare_records(records)
        if self.writer is None:
            table = pyarrow.Table.from_pylist(records)
            self.writer = pyarrow.parquet.ParquetWriter(
                self.fobj, table.schema, compression=self.compression, use_dictionary=False
            )
        else:
            normalized_records = self._normalize_records_to_schema(records, self.writer.schema)
            table = pyarrow.Table.from_pylist(normalized_records, schema=self.writer.schema)
        self.writer.write_table(table)

    def flush(self):
        """Flush all data"""
        if not self.__buffer:
            return
        self._write_records(self.__buffer)
        self.__buffer = []

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
        """Yield scanner batches, optionally projecting Parquet columns."""
        selection = selection or BatchSelection()
        if selection.predicate is not None or selection.table is not None:
            raise NotImplementedError("Parquet native batches support columns and row ranges, not predicates/tables")
        if selection.columns is not None and self.pos == 0 and not self._pending_rows:
            self._batch_iterator = self.reader.iter_batches(
                batch_size=selection.batch_size or self.batch_size,
                columns=list(selection.columns),
            )
        target = selection.batch_size or self.batch_size
        start, stop = selection.row_range or (0, None)
        if selection.slice is not None:
            slice_start, slice_stop, _step = selection.slice
            start = slice_start
            stop = slice_stop
        index = 0
        for batch in self._batch_iterator:
            rows = batch.to_pylist()
            selected: list[dict[str, Any]] = []
            for row in rows:
                if index >= start and (stop is None or index < stop):
                    selected.append(row)
                index += 1
            while selected:
                chunk, selected = selected[:target], selected[target:]
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

        if self.writer is not None:
            # Validate against the established schema before buffering so
            # callers still receive alignment errors at the offending batch,
            # while successful rows retain bounded row-group buffering.
            try:
                prepared = self._prepare_records(records)
                normalized = self._normalize_records_to_schema(prepared, self.writer.schema)
                pyarrow.Table.from_pylist(normalized, schema=self.writer.schema)
            except Exception as exc:
                raise WriteError(
                    "Failed to write records aligned to the existing Parquet schema "
                    f"({self.writer.schema.names}): {exc}",
                    filename=getattr(self, "filename", None),
                    error_code="SCHEMA_ALIGNMENT_FAILED",
                ) from exc

        # Always buffer to a bounded row group.  Previously a writer that had
        # already been created bypassed the buffer, producing one physical row
        # group per ``write`` call.
        self.__buffer.extend(records)
        if len(self.__buffer) >= self.row_group_size:
            self.flush()

    def write_batch(self, records: list[Row]) -> None:
        """Native batch writer hook used by columnar conversion."""
        self.write_bulk(records)
