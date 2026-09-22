"""Zarr v2/v3 array-store iterable.

Row mapping (see docs/docs/formats/zarr.md):

- Structured (named-field) arrays yield one dict per element keyed by field name.
- Dense 1-D arrays yield ``{"index": i, "value": scalar}``.
- Dense N-D arrays yield ``{"index": i, "values": row_slice}``.
- Scalar (0-d) arrays yield a single ``{"value": scalar}`` record.

Selection (``iterableargs`` or constructor kwargs):

- ``array``: array path inside the store (required when a store has >1 array).
- ``axis``: iteration axis (default 0); ``totals()`` counts selected rows on it.
- ``slice``: ``(start, stop, step)`` window along the iteration axis, applied
  before value conversion.
- ``fields`` (alias ``columns``): structured-array field projection.
- ``chunks``: write chunk size along the append axis; reads are bounded by the
  array's own chunk length along the iteration axis.

Object-dtype arrays (pickle-based codecs) are rejected by default on both read
and write; pass ``allow_object=True`` only for trusted stores.
"""

from __future__ import annotations

import math
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

_DENSE_VALUE_KEY = "value"
_DENSE_VALUES_KEY = "values"
_STRUCTURED_DEFAULT_NAME = "records"
_ARRAY_MODES = ("python", "numpy")

builtins_slice = slice  # __init__ has a ``slice`` kwarg; keep the builtin reachable


class ZarrIterable(BaseFileIterable):
    """Read or append one named Zarr array as rows.

    Reads are bounded by the array's chunk length along the iteration axis
    (or by the requested bulk size, whichever is larger). Writes buffer up to
    ``chunks`` records per flush and append along axis 0 of a created array.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        mode: str = "r",
        codec: BaseCodec | None = None,
        array: str | None = None,
        axis: int | None = None,
        slice: tuple[int | None, int | None, int | None] | None = None,
        fields: list[str] | tuple[str, ...] | None = None,
        chunks: int | None = None,
        dtype: Any = None,
        array_mode: str | None = None,
        allow_object: bool | None = None,
        zarr_format: int | None = None,
        storage_options: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ):
        if zarr is None or np is None:
            raise ImportError("Zarr support requires 'zarr' and 'numpy'. Install with: pip install iterabledata[zarr]")
        if stream is not None:
            raise ValueError("Zarr stores require a directory filename or store URL, not a stream")
        if filename is None:
            raise ValueError("Zarr stores require a directory filename or store URL")
        options = options or {}
        self.array_name = array if array is not None else options.get("array")
        self.axis = axis if axis is not None else options.get("axis", 0)
        row_slice = slice if slice is not None else options.get("slice")
        self.row_slice = self._normalize_slice(row_slice)
        if fields is None:
            fields = options.get("fields", options.get("columns"))
        self.fields = tuple(fields) if fields is not None else None
        self.chunk_size = max(1, chunks if chunks is not None else options.get("chunks", 1024))
        self.dtype = dtype if dtype is not None else options.get("dtype")
        self.array_mode = array_mode if array_mode is not None else options.get("array_mode", "python")
        if self.array_mode not in _ARRAY_MODES:
            raise ValueError(f"Invalid array_mode {self.array_mode!r}; expected one of {_ARRAY_MODES}")
        self.allow_object = bool(allow_object if allow_object is not None else options.get("allow_object", False))
        self.zarr_format = zarr_format if zarr_format is not None else options.get("zarr_format")
        if self.zarr_format not in (None, 2, 3):
            raise ValueError(f"zarr_format must be 2 or 3, got {self.zarr_format!r}")
        self.storage_options = storage_options if storage_options is not None else options.get("storage_options")
        self._buffer: deque[Row] = deque()
        self._rowbuf: deque[Row] = deque()
        self._array = None
        self._group = None
        self._axis = 0
        self._ndim = 0
        self._sel_start = 0
        self._sel_stop = 0
        self._sel_step = 1
        self._cursor = 0
        self._total = 0
        self._written = 0
        self._schema_fields: tuple[str, ...] | None = None
        self._dense_key: str | None = None
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, noopen=True, options=options or {})
        self.reset()

    # ------------------------------------------------------------------
    # Capabilities
    # ------------------------------------------------------------------

    @staticmethod
    def id() -> str:
        return "zarr"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_totals() -> bool:
        return True

    @staticmethod
    def has_tables() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    # ------------------------------------------------------------------
    # Store handling
    # ------------------------------------------------------------------

    @staticmethod
    def _is_url(path: Any) -> bool:
        return isinstance(path, str) and "://" in path

    @staticmethod
    def _normalize_slice(value: Any) -> tuple[int | None, int | None, int | None] | None:
        if value is None:
            return None
        if isinstance(value, slice):  # noqa: F821 - builtin at module scope
            return (value.start, value.stop, value.step)
        if isinstance(value, (tuple, list)) and 2 <= len(value) <= 3:
            start, stop = value[0], value[1]
            step = value[2] if len(value) == 3 else None
            return (start, stop, step)
        raise ValueError(f"Invalid slice selection {value!r}; expected (start, stop[, step])")

    def _open_group(self, mode: str):
        kwargs: dict[str, Any] = {"mode": mode, "storage_options": self.storage_options}
        if mode != "r" and self.zarr_format is not None:
            kwargs["zarr_format"] = self.zarr_format
        try:
            return zarr.open_group(self.filename, **kwargs)
        except Exception as exc:
            raise ValueError(f"Path is not a valid Zarr store or cannot be opened: {self.filename} ({exc})") from exc

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        self._buffer.clear()
        self._rowbuf.clear()
        if self.mode == "r":
            if not self._is_url(self.filename) and not os.path.isdir(self.filename):
                raise FileNotFoundError(f"Zarr store not found at: {self.filename}")
            self._group = self._open_group("r")
            names = self.list_tables()
            if self.array_name is None:
                if len(names) != 1:
                    raise ValueError(f"Zarr store contains multiple arrays; specify array= (available: {names})")
                self.array_name = names[0]
            if self.array_name not in names:
                raise KeyError(f"Zarr array {self.array_name!r} not found; available arrays: {names}")
            self._array = self._group[self.array_name]
            self._configure_selection()
        else:
            self._group = None
            self._array = None
            self._written = 0
            self._schema_fields = None
            self._dense_key = None

    def _configure_selection(self) -> None:
        arr = self._array
        dtype = arr.dtype
        if getattr(dtype, "hasobject", False) and not self.allow_object:
            raise ValueError(
                f"Zarr array {self.array_name!r} has object dtype; object codecs may deserialize "
                "untrusted data (e.g. pickle). Pass allow_object=True only for trusted stores."
            )
        self._ndim = len(arr.shape)
        if self._ndim == 0:
            if self.row_slice is not None:
                raise ValueError("slice selection is not applicable to scalar (0-d) Zarr arrays")
            if self.fields is not None:
                raise ValueError("fields selection is not applicable to scalar (0-d) Zarr arrays")
            self._axis = 0
            self._sel_start, self._sel_stop, self._sel_step = 0, 1, 1
        else:
            axis = self.axis
            if axis < 0:
                axis += self._ndim
            if not 0 <= axis < self._ndim:
                raise ValueError(f"axis {self.axis} out of range for Zarr array with {self._ndim} dimensions")
            self._axis = axis
            start, stop, step = self.row_slice or (None, None, None)
            start = 0 if start is None else start
            stop = arr.shape[self._axis] if stop is None else min(stop, arr.shape[self._axis])
            step = 1 if step is None else step
            if start < 0 or stop < 0:
                raise ValueError("Negative slice bounds are not supported for Zarr selection")
            if step <= 0:
                raise ValueError("slice step must be a positive integer")
            self._sel_start, self._sel_stop, self._sel_step = start, max(start, stop), step
        if self.fields is not None:
            names = dtype.names
            if not names:
                raise ValueError(
                    f"fields selection requires a structured Zarr array; {self.array_name!r} has dtype {dtype}"
                )
            unknown = [name for name in self.fields if name not in names]
            if unknown:
                raise KeyError(f"Unknown Zarr fields {unknown}; available fields: {list(names)}")
        self._total = math.ceil((self._sel_stop - self._sel_start) / self._sel_step)
        self._cursor = self._sel_start
        self.pos = 0

    def list_tables(self, filename: str | None = None) -> list[str]:
        if filename is None and self._group is not None:
            group = self._group
        else:
            path = filename or self.filename
            try:
                group = zarr.open_group(path, mode="r", storage_options=self.storage_options)
            except Exception as exc:
                raise ValueError(f"Path is not a valid Zarr store or cannot be opened: {path} ({exc})") from exc
        if hasattr(group, "array_keys"):
            return sorted(group.array_keys())
        return sorted(name for name, _value in group.arrays())

    def totals(self) -> int:
        if self.mode == "r":
            return self._total
        return self._written + len(self._buffer)

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def _convert(self, value: Any) -> Any:
        if self.array_mode == "numpy":
            return value
        return value.tolist() if hasattr(value, "tolist") else value

    def _row(self, index: int, item: Any) -> Row:
        dtype = self._array.dtype
        if dtype.names:
            fields = self.fields or dtype.names
            return {name: self._convert(item[name]) for name in fields}
        if self._ndim <= 1:
            return {"index": index, _DENSE_VALUE_KEY: self._convert(item)}
        return {"index": index, _DENSE_VALUES_KEY: self._convert(item)}

    def _fill(self, target: int) -> None:
        while len(self._rowbuf) < target and self._cursor < self._sel_stop:
            self._fetch_window()

    def _fetch_window(self) -> None:
        arr = self._array
        if self._ndim == 0:
            self._rowbuf.append({_DENSE_VALUE_KEY: self._convert(arr[()])})
            self._cursor = self._sel_stop
            return
        chunk_len = arr.chunks[self._axis] if arr.chunks else self._sel_stop
        end = min(self._cursor + max(1, chunk_len), self._sel_stop)
        index: list[Any] = [builtins_slice(None)] * self._ndim
        index[self._axis] = builtins_slice(self._cursor, end)
        window = np.asarray(arr[tuple(index)])
        if self._axis != 0:
            window = np.moveaxis(window, self._axis, 0)
        for offset, array_index in enumerate(range(self._cursor, end)):
            if (array_index - self._sel_start) % self._sel_step != 0:
                continue
            self._rowbuf.append(self._row(array_index, window[offset]))
        self._cursor = end

    def read(self, skip_empty: bool = True) -> Row:
        if self._array is None:
            raise StopIteration
        self._fill(1)
        if not self._rowbuf:
            raise StopIteration
        row = self._rowbuf.popleft()
        self.pos += 1
        return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[Row]:
        if self._array is None:
            return []
        self._fill(num)
        rows = []
        while self._rowbuf and len(rows) < num:
            rows.append(self._rowbuf.popleft())
        self.pos += len(rows)
        return rows

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------

    def write(self, record: Row) -> None:
        self.write_bulk([record])

    def write_bulk(self, records: list[Row]) -> None:
        for record in records:
            if not isinstance(record, dict):
                raise TypeError(f"Zarr records must be dicts, got {type(record).__name__}")
            self._buffer.append(record)
        if len(self._buffer) >= self.chunk_size:
            self.flush()

    def _records_to_array(self, records: list[Row]):
        """Convert buffered records to one numpy array, enforcing schema rules."""
        explicit_dtype = np.dtype(self.dtype) if self.dtype is not None else None
        if explicit_dtype is not None and explicit_dtype.names:
            return self._structured_batch(records, explicit_dtype.names, explicit_dtype)
        if self._schema_fields is not None:
            return self._structured_batch(records, self._schema_fields, None)
        if self.array_name is not None:
            values = []
            for record in records:
                if self.array_name not in record:
                    raise KeyError(f"Record does not contain configured Zarr array field {self.array_name!r}")
                values.append(record[self.array_name])
            return np.asarray(values, dtype=explicit_dtype)
        key_sets = {tuple(record.keys()) for record in records}
        if len(key_sets) != 1:
            raise ValueError(f"Zarr records in one batch must share the same field set; got {sorted(key_sets)}")
        keys = next(iter(key_sets))
        if len(keys) == 1:
            self._dense_key = keys[0]
            values = [record[keys[0]] for record in records]
            return np.asarray(values, dtype=explicit_dtype)
        return self._structured_batch(records, keys, explicit_dtype)

    def _structured_batch(self, records: list[Row], fields: tuple[str, ...], dtype: Any):
        for record in records:
            missing = [name for name in fields if name not in record]
            extra = [name for name in record if name not in fields]
            if missing or extra:
                raise ValueError(
                    f"Zarr structured record schema mismatch: expected fields {list(fields)}, "
                    f"missing {missing}, unexpected {extra}"
                )
        if dtype is None:
            columns = {name: np.asarray([record[name] for record in records]) for name in fields}
            dtype = [(name, columns[name].dtype) for name in fields]
        else:
            columns = {}
            for name in fields:
                column = np.asarray([record[name] for record in records])
                target = dtype.fields[name][0]
                if not np.can_cast(column.dtype, target, casting="safe"):
                    raise ValueError(
                        f"Zarr field {name!r} dtype mismatch: cannot safely cast {column.dtype} to {target}"
                    )
                columns[name] = column.astype(target, copy=False)
        batch = np.empty(len(records), dtype=dtype)
        for name in fields:
            batch[name] = columns[name]
        return batch

    def _check_object_dtype(self, dtype: Any) -> None:
        if getattr(dtype, "hasobject", False) and not self.allow_object:
            raise ValueError(
                "Zarr writes of object-dtype arrays are disabled by default because object codecs "
                "(e.g. pickle) can deserialize untrusted data. Pass allow_object=True and an explicit "
                "dtype to opt in for trusted data."
            )

    def _create_array(self, batch: Any) -> None:
        self._check_object_dtype(batch.dtype)
        if self._group is None:
            self._group = self._open_group("a")
        name = self.array_name
        if name is None:
            name = _STRUCTURED_DEFAULT_NAME if batch.dtype.names else (self._dense_key or _DENSE_VALUE_KEY)
            self.array_name = name
        if name in self.list_tables():
            del self._group[name]  # mode="w" truncates an existing array
        chunks = (min(self.chunk_size, max(1, len(batch))),) + batch.shape[1:]
        self._array = self._group.create_array(name, shape=(0,) + batch.shape[1:], chunks=chunks, dtype=batch.dtype)
        if batch.dtype.names:
            self._schema_fields = tuple(batch.dtype.names)

    def _check_compatible(self, batch: Any) -> Any:
        target = self._array
        if batch.ndim != target.ndim or tuple(batch.shape[1:]) != tuple(target.shape[1:]):
            raise ValueError(
                f"Zarr append shape mismatch: batch trailing shape {tuple(batch.shape[1:])} does not match "
                f"array shape {tuple(target.shape)}"
            )
        if target.dtype.names:
            if set(batch.dtype.names or ()) != set(target.dtype.names):
                raise ValueError(
                    f"Zarr append schema mismatch: batch fields {list(batch.dtype.names or ())} do not match "
                    f"array fields {list(target.dtype.names)}"
                )
            for name in target.dtype.names:
                if not np.can_cast(batch.dtype.fields[name][0], target.dtype.fields[name][0], casting="safe"):
                    raise ValueError(
                        f"Zarr field {name!r} dtype mismatch: cannot safely cast "
                        f"{batch.dtype.fields[name][0]} to {target.dtype.fields[name][0]}"
                    )
            batch = batch.astype(target.dtype)  # field-name-matched, verified safe above
        elif batch.dtype.names:
            raise ValueError(
                f"Zarr append schema mismatch: structured batch cannot append to dense array {self.array_name!r}"
            )
        elif not np.can_cast(batch.dtype, target.dtype, casting="safe"):
            raise ValueError(
                f"Zarr append dtype mismatch: cannot safely cast {batch.dtype} to {target.dtype}; "
                "pass an explicit dtype= at creation to choose a wider type"
            )
        self._check_object_dtype(batch.dtype)
        return batch

    def flush(self) -> None:
        if not self._buffer:
            return
        batch = self._records_to_array(list(self._buffer))
        if self._array is None:
            self._create_array(batch)
        batch = self._check_compatible(batch)
        old_size = self._array.shape[0]
        self._array.resize((old_size + len(batch),) + self._array.shape[1:])
        self._array[old_size:] = batch
        self._written += len(batch)
        self._buffer.clear()

    def close(self) -> None:
        if self.mode != "r":
            self.flush()
        super().close()
