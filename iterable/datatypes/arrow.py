from __future__ import annotations

import typing

try:
    import pyarrow
    import pyarrow.feather
    import pyarrow.ipc

    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False

from typing import Any

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..types import Row

DEFAULT_BATCH_SIZE = 1024


class ArrowIterable(BaseFileIterable):
    """Apache Arrow/Feather reader.

    Memory behavior: Arrow IPC / Feather v2 files are read batch by batch via
    ``pyarrow.ipc.open_file`` (record batches are loaded on demand, not the
    whole table). Legacy Feather v1 files have no batch reader and fall back
    to a full ``read_table()`` load.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        mode: str = "r",
        codec: BaseCodec | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_PYARROW:
            raise ImportError("Arrow/Feather support requires 'pyarrow' package")
        self.batch_size = batch_size
        self.__buffer = []
        self.is_data_written = False
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        self.reader = None
        self.table = None
        self._ipc_reader = None
        if self.mode == "r":
            try:
                # Arrow IPC / Feather v2: batches are loaded lazily on demand.
                self._ipc_reader = pyarrow.ipc.open_file(self.fobj)
            except pyarrow.lib.ArrowInvalid:
                # Legacy Feather v1 has no batch reader; full load is the
                # only option the library offers.
                self.fobj.seek(0)
                self.table = pyarrow.feather.read_table(self.fobj)
            self.iterator = self.__iterator()
            # Independent batch iterator for optimized bulk reads
            self._batch_iterator = self._batches()
            self._cached_batch = []  # Cache for remaining rows from a batch
        self.writer = None
        if self.mode == "w":
            self.writer = None  # Will be created on first write

    def _batches(self):
        """Yield record batches lazily (IPC path) or from the loaded table."""
        if self._ipc_reader is not None:
            for i in range(self._ipc_reader.num_record_batches):
                yield self._ipc_reader.get_batch(i)
        else:
            yield from self.table.to_batches(max_chunksize=self.batch_size)

    @staticmethod
    def id() -> str:
        return "arrow"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        """Streams batch by batch for Arrow IPC files; Feather v1 is full-load."""
        return self._ipc_reader is not None

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if self.mode == "r":
            if self._ipc_reader is not None:
                reader = self._ipc_reader
                return sum(reader.get_batch(i).num_rows for i in range(reader.num_record_batches))
            return len(self.table)
        return 0

    def flush(self):
        """Flush all data"""
        if len(self.__buffer) > 0:
            batch = pyarrow.RecordBatch.from_pylist(self.__buffer)
            # Arrow IPC file format (= Feather v2); replaces the deprecated
            # pyarrow.feather.write_feather and is batch-readable on reread.
            with pyarrow.ipc.new_file(self.fobj, batch.schema) as writer:
                writer.write_batch(batch)
            self.__buffer = []

    def close(self):
        """Close iterable"""
        if self.mode == "w" and len(self.__buffer) > 0:
            self.flush()
        super().close()

    def __iterator(self):
        """Iterator for reading records"""
        for batch in self._batches():
            yield from batch.to_pylist()

    def read(self, skip_empty: bool = True) -> dict:
        """Read single record"""
        row = next(self.iterator)
        self.pos += 1
        return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk Arrow records efficiently using batch reading.

        This optimized implementation directly consumes batches from to_batches()
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
        self.__buffer.extend(records)
