from __future__ import annotations

import typing
from collections import deque

try:
    import pyarrow
    import pyarrow.feather
    import pyarrow.ipc

    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False

from typing import Any

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..convert.batch import BatchSelection
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
    supports_native_batch = True

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
            self._batch_iterator = self._batches()
            self._pending_rows = deque()
        self.writer = None
        self._ipc_writer = None
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
            # Keep a single IPC writer for the output. Re-opening a file
            # writer for every flush writes repeated IPC headers and makes
            # row-at-a-time writes needlessly expensive.
            if self._ipc_writer is None:
                self._ipc_writer = pyarrow.ipc.new_file(self.fobj, batch.schema)
            self._ipc_writer.write_batch(batch)
            self.__buffer = []

    def close(self):
        """Close iterable"""
        if self.mode == "w" and len(self.__buffer) > 0:
            self.flush()
        if self._ipc_writer is not None:
            self._ipc_writer.close()
            self._ipc_writer = None
        super().close()

    def _fill_pending_rows(self) -> bool:
        """Load one record batch into the shared row cursor."""
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
        """Read bulk Arrow records efficiently using batch reading.

        This optimized implementation directly consumes batches from to_batches()
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
        """Yield Arrow record batches with optional projection and slicing."""
        selection = selection or BatchSelection()
        if selection.predicate is not None or selection.table is not None:
            raise NotImplementedError("Arrow native batches support columns and row ranges, not predicates/tables")
        target = selection.batch_size or self.batch_size
        start, stop = selection.row_range or (0, None)
        if selection.slice is not None:
            slice_start, slice_stop, _step = selection.slice
            start = slice_start
            stop = slice_stop
        index = 0
        for batch in self._batch_iterator:
            if selection.columns is not None:
                batch = batch.select(list(selection.columns))
            rows = batch.to_pylist()
            selected = []
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
        self.__buffer.extend(records)
        if len(self.__buffer) >= self.batch_size:
            self.flush()

    def write_batch(self, records: list[Row]) -> None:
        """Native batch writer hook used by columnar conversion."""
        self.write_bulk(records)
