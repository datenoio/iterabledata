import typing
from typing import Any

from ..base import BaseFileIterable
from ..exceptions import WriteNotSupportedError
from ..types import Row

try:
    import dpkt

    HAS_DPKT = True
except ImportError:
    HAS_DPKT = False


class PCAPIterable(BaseFileIterable):
    """PCAP iterable"""

    datamode = "binary"

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec=None,
        binary: bool = True,
        encoding: str | None = None,
        noopen: bool = False,
        mode: str = "r",
        options: dict[str, Any] | None = None,
    ):
        if not HAS_DPKT:
            raise ImportError("dpkt is required for PCAP support. Install with 'pip install iterabledata[pcap]'")
        super().__init__(
            filename, stream, codec, binary=True, encoding=encoding, noopen=noopen, mode=mode, options=options
        )
        self.reader = None
        self._iter = None

    @staticmethod
    def id() -> str:
        return "pcap"

    def reset(self):
        super().reset()
        self.reader = None
        self._iter = None

    def read(self, skip_empty: bool = True) -> Row:
        if self._iter is None:
            self._iter = iter(self)
        timestamp, buf = next(self._iter)
        return {"timestamp": timestamp, "data": buf}

    def __iter__(self):
        if self.fobj is None:
            self.open()

        # Determine if it's pcap or pcapng based on magic bytes or just try pcap first
        # dpkt doesn't auto-detect easily from stream, but we can try.
        # However, for now, let's assume pcap.Reader. pcapng.Reader is also available.
        # A simple heuristic check could be useful, or we trust dpkt.

        try:
            self.reader = dpkt.pcap.Reader(self.fobj)
        except (ValueError, dpkt.dpkt.NeedData):
            # Fallback for pcapng or invalid
            try:
                self.fobj.seek(0)
                self.reader = dpkt.pcapng.Reader(self.fobj)
            except Exception:
                # If simple pcap failed, it might have been really pcap but empty/corrupt,
                # or it was pcapng and that failed too.
                # Raise the original error or a generic one.
                self.fobj.seek(0)
                self.reader = dpkt.pcap.Reader(self.fobj)

        yield from self.reader

    def write(self, record: Row) -> None:
        raise WriteNotSupportedError("pcap", "Writing PCAP files is not yet implemented")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("pcap", "Writing PCAP files is not yet implemented")
