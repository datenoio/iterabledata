"""Zarr v2/v3 array-store iterable."""

from __future__ import annotations

import os
import typing
from collections import deque
from typing import Any

try:
    import numpy as np
    import zarr
except ImportError:
    np = None
    zarr = None

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..types import Row


class ZarrIterable(BaseFileIterable):
    """Read or append one named Zarr array as rows.

    A row is ``{"value": scalar}`` for one-dimensional arrays and
    ``{"value": list}`` for higher-dimensional arrays. Stores containing more
    than one array require an explicit ``array=`` name.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        mode: str = "r",
        codec: BaseCodec | None = None,
        array: str | None = None,
        chunks: int = 1024,
        dtype: str | None = None,
        options: dict[str, Any] | None = None,
    ):
        if zarr is None or np is None:
            raise ImportError("Zarr support requires 'zarr' and 'numpy'. Install with: pip install iterabledata[zarr]")
        if stream is not None:
            raise ValueError("Zarr stores require a directory filename, not a stream")
        if filename is None:
            raise ValueError("Zarr stores require a directory filename")
        self.array_name = array
        self.chunk_size = max(1, chunks)
        self.dtype = dtype
        self._buffer: deque[Any] = deque()
        self._array = None
        self._group = None
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, noopen=True, options=options or {})
        self.reset()

    @staticmethod
    def id() -> str:
        return "zarr"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_totals() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        self._buffer.clear()
        if self.mode == "r":
            if not os.path.isdir(self.filename):
                raise FileNotFoundError(f"Zarr store not found at: {self.filename}")
            self._group = zarr.open_group(self.filename, mode="r")
            names = self.list_tables()
            if self.array_name is None:
                if len(names) != 1:
                    raise ValueError(f"Zarr store contains multiple arrays; specify array= (available: {names})")
                self.array_name = names[0]
            if self.array_name not in names:
                raise KeyError(f"Zarr array {self.array_name!r} not found; available arrays: {names}")
            self._array = self._group[self.array_name]
        else:
            self._group = None
            self._array = None

    def list_tables(self, filename: str | None = None) -> list[str]:
        path = filename or self.filename
        group = self._group if filename is None else zarr.open_group(path, mode="r")
        if group is None:
            return []
        if hasattr(group, "array_keys"):
            return sorted(group.array_keys())
        return sorted(name for name, _value in group.arrays())

    def totals(self) -> int:
        return int(self._array.shape[0]) if self._array is not None else len(self._buffer)

    @staticmethod
    def _row(value: Any) -> Row:
        value = value.tolist() if hasattr(value, "tolist") else value
        return {"value": value}

    def read(self, skip_empty: bool = True) -> Row:
        if self._array is None or self.pos >= self._array.shape[0]:
            raise StopIteration
        row = self._row(self._array[self.pos])
        self.pos += 1
        return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[Row]:
        if self._array is None or self.pos >= self._array.shape[0]:
            return []
        end = min(self.pos + num, self._array.shape[0])
        values = self._array[self.pos : end]
        rows = [self._row(value) for value in values]
        self.pos = end
        return rows

    def write(self, record: Row) -> None:
        self.write_bulk([record])

    def write_bulk(self, records: list[Row]) -> None:
        self._buffer.extend(records)
        if len(self._buffer) >= self.chunk_size:
            self.flush()

    def flush(self) -> None:
        if not self._buffer:
            return
        values = []
        for record in self._buffer:
            if self.array_name is None:
                if len(record) != 1:
                    raise ValueError("Zarr writes require array= for records with multiple fields")
                values.append(next(iter(record.values())))
            else:
                if self.array_name not in record:
                    raise KeyError(f"Record does not contain configured Zarr array field {self.array_name!r}")
                values.append(record[self.array_name])
        array_values = np.asarray(values, dtype=self.dtype)
        if self._array is None:
            if self.array_name is None:
                self.array_name = "value"
            self._array = zarr.open_array(
                os.path.join(self.filename, self.array_name),
                mode="w",
                shape=(0,) + array_values.shape[1:],
                chunks=(min(self.chunk_size, max(1, len(array_values))),) + array_values.shape[1:],
                dtype=array_values.dtype,
            )
        old_size = self._array.shape[0]
        self._array.resize((old_size + len(array_values),) + self._array.shape[1:])
        self._array[old_size:] = array_values
        self._buffer.clear()

    def close(self) -> None:
        if self.mode != "r":
            self.flush()
        super().close()
