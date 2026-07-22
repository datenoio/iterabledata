"""SEG-Y seismic trace reader.

Uses optional ``segyio`` when available. Yields one record per trace::

    {"trace_index": 0, "samples": [...], ...header fields...}

Install with::

    pip install segyio

Read-only. Format id: ``segy``.
"""

from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteNotSupportedError
from ..types import Row

try:
    import segyio  # type: ignore[import-untyped]

    HAS_SEGYIO = True
except ImportError:
    HAS_SEGYIO = False

_IMPORT_ERROR = (
    "SEG-Y support requires 'segyio'. Install with: pip install segyio "
    "(or pip install iterabledata[seismic] when that extra is configured)"
)


class SEGYIterable(BaseFileIterable):
    """Read-only SEG-Y trace iterable."""

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
        if not HAS_SEGYIO:
            raise ImportError(_IMPORT_ERROR)
        if mode not in ("r", "rb"):
            raise WriteNotSupportedError("segy", "SEG-Y is read-only")
        if filename is None:
            raise ReadError(
                "SEG-Y reading requires a filename",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        if stream is not None or codec is not None:
            raise ReadError(
                "SEG-Y reading requires a filename, not a stream or codec",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        self._ignore_geometry = bool(options.pop("ignore_geometry", True))
        super().__init__(
            filename=filename,
            stream=None,
            codec=None,
            binary=True,
            mode="r",
            noopen=True,
            options=options,
        )
        self._file: Any = None
        self._index = 0
        self._n_traces = 0
        self.reset()

    @staticmethod
    def id() -> str:
        return "segy"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    def reset(self) -> None:
        self.pos = 0
        self._index = 0
        assert self.filename is not None
        if self._file is not None:
            try:
                self._file.close()
            except Exception:
                pass
        self._file = segyio.open(self.filename, "r", ignore_geometry=self._ignore_geometry)
        self._n_traces = self._file.tracecount

    def read(self, skip_empty: bool = True) -> Row:
        if self._file is None or self._index >= self._n_traces:
            raise StopIteration
        samples = self._file.trace[self._index]
        header = self._file.header[self._index]
        record: dict[str, Any] = {
            "trace_index": self._index,
            "samples": samples.tolist() if hasattr(samples, "tolist") else list(samples),
        }
        # Include a few common header fields when present
        try:
            record["inline"] = int(header[segyio.TraceField.INLINE_3D])
            record["crossline"] = int(header[segyio.TraceField.CROSSLINE_3D])
        except Exception:
            pass
        self._index += 1
        self.pos += 1
        return record

    def close(self) -> None:
        if getattr(self, "_closed", False):
            return
        if self._file is not None:
            try:
                self._file.close()
            except Exception:
                pass
            self._file = None
        super().close()

    def write(self, record: Row) -> None:
        raise WriteNotSupportedError("segy", "SEG-Y is read-only")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("segy", "SEG-Y is read-only")
