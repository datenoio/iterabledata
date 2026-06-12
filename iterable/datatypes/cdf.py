"""NASA Common Data Format (CDF) support via spacepy.pycdf."""

from __future__ import annotations

import typing

try:
    from spacepy import pycdf

    HAS_PYCDF = True
except ImportError:
    HAS_PYCDF = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteNotSupportedError


def _to_python(val: Any) -> Any:
    """Convert CDF/NumPy values to Python-native types for records."""
    if val is None:
        return None
    try:
        import numpy as np

        if np.ma.is_masked(val):
            return None
        if isinstance(val, np.generic):
            return val.item()
        if isinstance(val, (bytes, bytearray)):
            return val.decode("utf-8", "ignore")
        if hasattr(val, "tolist"):
            return val.tolist()
    except ImportError:
        pass
    return val


class CDFIterable(BaseFileIterable):
    """Iterable over NASA Common Data Format (CDF) files by record index."""

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_PYCDF:
            raise ImportError(
                "CDF support requires the 'spacepy' package and the NASA CDF C library. "
                "Install with: pip install iterabledata[cdf]. "
                "See https://cdf.gsfc.nasa.gov for the CDF C library."
            )
        self.options = options
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.reset()

    def reset(self) -> None:
        """Reset iterable and reopen CDF for reading."""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            path = self.filename
            if not path and hasattr(self.fobj, "name"):
                path = self.fobj.name
            if not path:
                raise ReadError(
                    "CDF reading requires a filename or a file object with a name attribute",
                    filename=None,
                    error_code="RESOURCE_REQUIREMENT_NOT_MET",
                )
            try:
                self._cdf = pycdf.CDF(path)
            except Exception as e:
                raise ReadError(
                    f"Failed to open CDF file: {e}",
                    filename=path,
                    error_code="OPEN_FAILED",
                ) from e
            self.iterator = self._record_iterator()
        else:
            raise WriteNotSupportedError("cdf", "CDF writing is not supported")

    def _record_iterator(self) -> typing.Iterator[dict[str, Any]]:
        """Yield one dict per CDF record (record-varying dimension)."""
        cdf = self._cdf
        var_names = list(cdf.keys())
        if not var_names:
            return

        # Get record count from first variable (record-varying vars have length)
        try:
            first_var = cdf[var_names[0]]
            n_records = len(first_var)
        except (TypeError, Exception):
            n_records = 1
        if n_records == 0:
            n_records = 1

        for i in range(n_records):
            record = {}
            for name in var_names:
                var = cdf[name]
                try:
                    val = var[i]
                    record[name] = _to_python(val)
                except (IndexError, KeyError, TypeError, Exception):
                    try:
                        val = var[...]
                        record[name] = _to_python(val)
                    except Exception:
                        record[name] = None
            yield record

    @staticmethod
    def id() -> str:
        return "cdf"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    @staticmethod
    def has_tables() -> bool:
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List variable names in the CDF file."""
        if filename is None and hasattr(self, "_cdf") and self._cdf is not None:
            return list(self._cdf.keys())
        path = filename if filename is not None else self.filename
        if path is None:
            return None
        try:
            with pycdf.CDF(path, readonly=True) as cdf:
                return list(cdf.keys())
        except Exception:
            return None

    def close(self) -> None:
        if hasattr(self, "_cdf") and self._cdf is not None:
            try:
                self._cdf.close()
            except Exception:
                pass
            self._cdf = None
        super().close()

    def read(self, skip_empty: bool = True) -> dict[str, Any]:
        row = next(self.iterator)
        self.pos += 1
        return row
