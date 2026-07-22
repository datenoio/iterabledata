"""MATLAB .mat format reader (scipy / optional h5py for v7.3)."""

from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteNotSupportedError
from ..types import Row

try:
    from scipy.io import loadmat as _scipy_loadmat

    HAS_SCIPY = True
except ImportError:
    _scipy_loadmat = None
    HAS_SCIPY = False

try:
    import h5py as _h5py

    HAS_H5PY = True
except ImportError:
    _h5py = None
    HAS_H5PY = False

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore[assignment]
    HAS_NUMPY = False


def _is_meta_key(name: str) -> bool:
    return name.startswith("__")


class MATIterable(BaseFileIterable):
    """Read MATLAB ``.mat`` variables as row dictionaries.

    Uses ``scipy.io.loadmat`` when available. For MATLAB v7.3 (HDF5-based)
    files, falls back to ``h5py`` when scipy cannot load them.

    - ``list_tables()`` returns variable names (excluding ``__*`` metadata).
    - When multiple variables exist, pass ``options={"table": name}`` or
      ``options={"variable": name}`` (or the ``table`` / ``variable`` kwarg).
    - 1D arrays yield ``{"value": v}``; 2D arrays yield ``{"col0": ..., "col1": ...}``.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        table: str | None = None,
        variable: str | None = None,
        options: dict[str, Any] | None = None,
    ):
        if not HAS_SCIPY:
            raise ImportError("MAT support requires 'scipy'. Install with: pip install iterabledata[mat]")
        if options is None:
            options = {}
        if stream is not None or codec is not None:
            raise ReadError(
                "MAT file reading requires filename (not stream or codec)",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        if filename is None:
            raise ReadError(
                "MAT file reading requires filename",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        if mode not in ("r", "rb"):
            raise WriteNotSupportedError("mat", "MAT file writing is not supported")
        self.table_name = options.get("table", options.get("variable", table if table is not None else variable))
        self._variables: dict[str, Any] = {}
        self._array = None
        self._iterator: typing.Iterator[Row] | None = None
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, noopen=True, options=options)
        self.pos = 0
        self.reset()

    def reset(self) -> None:
        """Reload MAT variables and select the active array."""
        super().reset()
        self.pos = 0
        if self.mode != "r":
            raise WriteNotSupportedError("mat", "MAT file writing is not supported")
        self._variables = self._load_variables(self.filename)
        names = [n for n in self._variables if not _is_meta_key(n)]
        if not names:
            raise ValueError(f"MAT file {self.filename!r} contains no variables")
        selected = self.table_name
        if selected is None:
            if len(names) != 1:
                raise ValueError(
                    f"MAT file contains multiple variables; specify table= or variable= (available: {names})"
                )
            selected = names[0]
        elif selected not in names:
            raise ValueError(f"Variable {selected!r} not found in MAT file; available: {names}")
        self.table_name = selected
        self._array = self._variables[selected]
        self._iterator = self._yield_rows(self._array)

    def _load_variables(self, filename: str) -> dict[str, Any]:
        try:
            data = _scipy_loadmat(filename, squeeze_me=False, struct_as_record=False)
            return {k: v for k, v in data.items() if not _is_meta_key(k)}
        except NotImplementedError:
            return self._load_v73(filename)
        except ValueError as exc:
            # scipy raises ValueError for some v7.3 files
            msg = str(exc).lower()
            if "hdf" in msg or "7.3" in msg or "h5py" in msg:
                return self._load_v73(filename)
            raise
        except Exception as exc:  # noqa: BLE001 - detect v7.3 via message
            msg = str(exc).lower()
            if "hdf" in msg or "7.3" in msg:
                return self._load_v73(filename)
            raise

    def _load_v73(self, filename: str) -> dict[str, Any]:
        if not HAS_H5PY:
            raise ImportError("MATLAB v7.3 .mat files require 'h5py'. Install with: pip install iterabledata[mat]")
        variables: dict[str, Any] = {}
        with _h5py.File(filename, "r") as handle:
            for key in handle.keys():
                if _is_meta_key(key):
                    continue
                item = handle[key]
                if hasattr(item, "shape"):
                    variables[key] = item[()]
        return variables

    @staticmethod
    def _to_python(value: Any) -> Any:
        if hasattr(value, "item") and getattr(value, "ndim", 1) == 0:
            return value.item()
        if HAS_NUMPY and isinstance(value, np.generic):
            return value.item()
        return value

    def _yield_rows(self, array: Any) -> typing.Iterator[Row]:
        if array is None:
            return
        # Convert cell/object arrays and matlab matrices to ndarray when possible
        if HAS_NUMPY and not isinstance(array, np.ndarray):
            try:
                array = np.asarray(array)
            except (TypeError, ValueError):
                yield {"value": array}
                return

        if not HAS_NUMPY:
            # Fallback without numpy: treat as nested lists
            if isinstance(array, (list, tuple)):
                if array and isinstance(array[0], (list, tuple)):
                    for row in array:
                        yield {f"col{j}": row[j] for j in range(len(row))}
                else:
                    for v in array:
                        yield {"value": v}
                return
            yield {"value": array}
            return

        arr = np.asarray(array)
        # scipy often loads column vectors as (n, 1)
        if arr.ndim == 2 and 1 in arr.shape:
            arr = arr.reshape(-1)
        if arr.ndim == 0:
            yield {"value": self._to_python(arr)}
            return
        if arr.ndim == 1:
            for v in arr:
                yield {"value": self._to_python(v)}
            return
        if arr.ndim == 2:
            for i in range(arr.shape[0]):
                row = arr[i]
                yield {f"col{j}": self._to_python(row[j]) for j in range(arr.shape[1])}
            return
        raise ValueError(f"Only 1D and 2D MAT arrays are supported for iteration, got shape {arr.shape}")

    @staticmethod
    def id() -> str:
        return "mat"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_tables() -> bool:
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List variable names in a MAT file (excluding ``__*`` metadata)."""
        target = filename if filename is not None else self.filename
        if target is None:
            return None
        if filename is None and self._variables:
            return sorted(self._variables.keys())
        variables = self._load_variables(target)
        return sorted(variables.keys())

    @staticmethod
    def has_totals() -> bool:
        return True

    def totals(self) -> int:
        if self._array is None:
            return 0
        if HAS_NUMPY:
            arr = np.asarray(self._array)
            if arr.ndim == 0:
                return 1
            if arr.ndim == 2 and 1 in arr.shape:
                return int(arr.size)
            return int(arr.shape[0])
        if isinstance(self._array, (list, tuple)):
            return len(self._array)
        return 1

    def read(self, skip_empty: bool = True) -> Row:
        """Read a single row from the selected MAT variable."""
        try:
            row = next(self._iterator)  # type: ignore[arg-type]
            self.pos += 1
            return row
        except (StopIteration, TypeError):
            raise StopIteration from None

    def write(self, record: Row) -> None:
        raise WriteNotSupportedError("mat", "MAT file writing is not supported")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("mat", "MAT file writing is not supported")
