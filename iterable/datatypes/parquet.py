from __future__ import annotations

import typing
from typing import Any

import pyarrow
import pyarrow.parquet

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..types import Row

DEFAULT_BATCH_SIZE = 1024


def fields_to_pyarrow_schema(keys):
    fields = []
    for key in keys:
        fields.append((key, pyarrow.string()))
    return pyarrow.schema(fields)


class ParquetIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        mode: str = "r",
        codec: BaseCodec | None = None,
        keys: list[str] | None = None,
        schema: list[str] = None,
        compression: str = "snappy",
        adapt_schema: bool = True,
        use_pandas: bool = True,
        batch_size: int = DEFAULT_BATCH_SIZE,
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
            self.reader = pyarrow.parquet.ParquetFile(self.fobj)
            self.iterator = self.__iterator()
            # Initialize batch iterator for optimized bulk reads
            self._batch_iterator = self.reader.iter_batches(batch_size=self.batch_size)
            self._cached_batch = []  # Cache for remaining rows from a batch
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

    def flush(self):
        """Flush all data"""
        if not self.__buffer:
            return
        table = pyarrow.Table.from_pylist(self.__buffer)
        if self.writer is None:
            self.writer = pyarrow.parquet.ParquetWriter(
                self.fobj, table.schema, compression=self.compression, use_dictionary=False
            )
        self.writer.write_table(table)
        self.__buffer = []

    def close(self):
        """Close iterable"""
        if self.mode == "w":
            self.flush()
        if self.writer is not None:
            self.writer.close()
        super().close()

    def __iterator(self):
        for batch in self.reader.iter_batches(batch_size=self.batch_size):
            yield from batch.to_pylist()

    def read(self, skip_empty: bool = True) -> dict:
        """Read single record"""
        row = next(self.iterator)
        self.pos += 1
        return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk Parquet records efficiently using batch reading.

        This optimized implementation directly consumes batches from iter_batches()
        instead of calling read() in a loop, providing significant performance
        improvements for columnar data access.
        """
        chunk = []

        # First, consume from cached batch if available
        if hasattr(self, "_cached_batch") and self._cached_batch:
            while len(chunk) < num and self._cached_batch:
                chunk.append(self._cached_batch.pop(0))
                self.pos += 1

        # If we need more rows, read from batches directly
        while len(chunk) < num:
            try:
                # Get next batch from batch iterator
                batch = next(self._batch_iterator)
                batch_rows = batch.to_pylist()

                # Add rows from batch to chunk
                remaining = num - len(chunk)
                chunk.extend(batch_rows[:remaining])
                self.pos += len(batch_rows[:remaining])

                # Cache remaining rows from batch for next read_bulk() call
                if len(batch_rows) > remaining:
                    if not hasattr(self, "_cached_batch"):
                        self._cached_batch = []
                    self._cached_batch = batch_rows[remaining:]
                else:
                    self._cached_batch = []

            except StopIteration:
                # No more batches available
                break

        return chunk

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

        # If we already have a writer, normalize records to match existing schema
        if self.writer is not None:
            # Get expected fields from existing schema
            expected_fields = {field.name for field in self.writer.schema}

            # Normalize records to match existing schema
            # Add missing fields as None, remove extra fields
            normalized_records = []
            for record in records:
                normalized = {}
                for field_name in expected_fields:
                    normalized[field_name] = record.get(field_name)
                normalized_records.append(normalized)

            try:
                table = pyarrow.Table.from_pylist(normalized_records)
                self.writer.write_table(table)
                return
            except Exception:
                # If normalization didn't work, buffer and let flush handle it
                # This can happen if there are type mismatches
                self.__buffer.extend(normalized_records)
                if len(self.__buffer) >= self.batch_size:
                    self.flush()
                return

        # Schema-adaptive streaming: buffer up to batch_size, then flush (writer created on first flush).
        self.__buffer.extend(records)
        if len(self.__buffer) >= self.batch_size:
            self.flush()
