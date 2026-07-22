"""fst columnar frame reader (experimental).

The ``fst`` format is an R on-disk columnar frame. There is no mature pure-Python
reader; this module attempts to use an optional ``fst`` (or ``rfst``) binding if
installed. Without that dependency, construction raises ``ImportError``.

Note: subprocess invocation of R is intentionally not supported.

Install guidance depends on the binding available in your environment; tests
skip when the dependency is missing.

Read-only. Format id: ``fst``. Requires a filename (not stream-only).
"""

from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteNotSupportedError
from ..types import Row

_FST_MOD: Any = None
_FST_BACKEND: str | None = None

try:
    import fst as _fst_pkg  # type: ignore[import-untyped]

    _FST_MOD = _fst_pkg
    _FST_BACKEND = "fst"
except ImportError:
    try:
        import rfst as _rfst_pkg  # type: ignore[import-untyped]

        _FST_MOD = _rfst_pkg
        _FST_BACKEND = "rfst"
    except ImportError:
        _FST_MOD = None
        _FST_BACKEND = None

HAS_FST = _FST_MOD is not None

_IMPORT_ERROR = (
    "fst support requires an optional Python binding such as the 'fst' or 'rfst' "
    "package (typically wrapping the R fst library). "
    "There is no pure-Python fst reader in IterableData. "
    "Install a compatible binding for your platform, or skip fst formats."
)


class FSTIterable(BaseFileIterable):
    """Read-only fst frame iterable (requires optional ``fst``/``rfst`` binding)."""

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
        if not HAS_FST:
            raise ImportError(_IMPORT_ERROR)
        if mode not in ("r", "rb"):
            raise WriteNotSupportedError("fst", "fst is read-only")
        if filename is None:
            raise ReadError(
                "fst reading requires a filename (stream/codec not supported)",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        if stream is not None or codec is not None:
            raise ReadError(
                "fst reading requires a filename, not a stream or codec",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        self._columns = options.pop("columns", None)
        super().__init__(
            filename=filename,
            stream=None,
            codec=None,
            binary=True,
            mode="r",
            noopen=True,
            options=options,
        )
        self._rows: list[dict[str, Any]] = []
        self._iterator: typing.Iterator[dict[str, Any]] | None = None
        self.reset()

    @staticmethod
    def id() -> str:
        return "fst"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return False

    def _load_frame(self, path: str) -> list[dict[str, Any]]:
        assert _FST_MOD is not None
        mod = _FST_MOD
        # Try common APIs across bindings.
        df = None
        if hasattr(mod, "read_fst"):
            kwargs: dict[str, Any] = {}
            if self._columns is not None:
                kwargs["columns"] = self._columns
            df = mod.read_fst(path, **kwargs)
        elif hasattr(mod, "read"):
            df = mod.read(path)
        elif hasattr(mod, "FSTFile"):
            df = mod.FSTFile(path).to_pandas()
        else:
            raise ImportError(
                f"Installed '{_FST_BACKEND}' package does not expose a known read API "
                f"(expected read_fst/read/FSTFile). {_IMPORT_ERROR}"
            )

        if hasattr(df, "to_dict"):
            records = df.to_dict("records")
            return [{k: (v.item() if hasattr(v, "item") else v) for k, v in row.items()} for row in records]
        if isinstance(df, list):
            return [dict(r) for r in df]
        raise ReadError(
            f"Unexpected fst read result type: {type(df)!r}",
            filename=path,
            error_code="FORMAT_PARSE_ERROR",
        )

    def reset(self) -> None:
        self.pos = 0
        assert self.filename is not None
        self._rows = self._load_frame(self.filename)
        self._iterator = iter(self._rows)

    def read(self, skip_empty: bool = True) -> Row:
        if self._iterator is None:
            raise StopIteration
        row = next(self._iterator)
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        raise WriteNotSupportedError("fst", "fst is read-only")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("fst", "fst is read-only")
