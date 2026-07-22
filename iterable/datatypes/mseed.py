"""MiniSEED waveform reader.

Uses optional ``obspy`` when available. Yields one record per trace::

    {
        "station": "...",
        "channel": "...",
        "starttime": "...",
        "sampling_rate": 100.0,
        "data": [...],
    }

Install with::

    pip install obspy

Read-only. Format id: ``mseed``.
"""

from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteNotSupportedError
from ..types import Row

try:
    from obspy import read as obspy_read  # type: ignore[import-untyped]

    HAS_OBSPY = True
except ImportError:
    HAS_OBSPY = False

_IMPORT_ERROR = (
    "miniSEED support requires 'obspy'. Install with: pip install obspy "
    "(or pip install iterabledata[seismo] when that extra is configured)"
)


class MiniSEEDIterable(BaseFileIterable):
    """Read-only MiniSEED trace iterable."""

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
        if not HAS_OBSPY:
            raise ImportError(_IMPORT_ERROR)
        if mode not in ("r", "rb"):
            raise WriteNotSupportedError("mseed", "miniSEED is read-only")
        if filename is None and stream is None and codec is None:
            raise ReadError(
                "miniSEED reading requires a filename, stream, or codec",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        super().__init__(
            filename=filename,
            stream=stream,
            codec=codec,
            binary=True,
            mode="r",
            options=options,
        )
        self._traces: list[dict[str, Any]] = []
        self._iterator: typing.Iterator[dict[str, Any]] | None = None
        self.reset()

    @staticmethod
    def id() -> str:
        return "mseed"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return False

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        if self.filename:
            st = obspy_read(self.filename, format="MSEED")
        else:
            # Stream / codec: buffer bytes for obspy
            data = self.fobj.read()
            from io import BytesIO

            st = obspy_read(BytesIO(data), format="MSEED")
        self._traces = []
        for tr in st:
            self._traces.append(
                {
                    "station": tr.stats.station,
                    "channel": tr.stats.channel,
                    "starttime": str(tr.stats.starttime),
                    "sampling_rate": float(tr.stats.sampling_rate),
                    "data": tr.data.tolist() if hasattr(tr.data, "tolist") else list(tr.data),
                    "network": getattr(tr.stats, "network", None),
                    "location": getattr(tr.stats, "location", None),
                }
            )
        self._iterator = iter(self._traces)

    def read(self, skip_empty: bool = True) -> Row:
        if self._iterator is None:
            raise StopIteration
        row = next(self._iterator)
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        raise WriteNotSupportedError("mseed", "miniSEED is read-only")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("mseed", "miniSEED is read-only")
