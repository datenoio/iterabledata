from __future__ import annotations

import typing
from collections.abc import Iterator
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import WriteNotSupportedError
from ..types import Row

try:
    import dpkt

    HAS_DPKT = True
except ImportError:
    HAS_DPKT = False


class PCAPIterable(BaseFileIterable):
    """PCAP / PCAP-NG packet capture iterable."""

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        binary: bool = True,
        encoding: str | None = None,
        noopen: bool = False,
        mode: str = "r",
        options: dict[str, Any] | None = None,
    ) -> None:
        if not HAS_DPKT:
            raise ImportError("dpkt is required for PCAP support. Install with 'pip install iterabledata[pcap]'")
        super().__init__(
            filename, stream, codec, binary=True, encoding=encoding, noopen=noopen, mode=mode, options=options
        )
        self.reader: Any = None
        self._packet_iter: Iterator[tuple[Any, bytes]] | None = None

    @staticmethod
    def id() -> str:
        return "pcap"

    def reset(self) -> None:
        super().reset()
        self.reader = None
        self._packet_iter = None

    def _open_reader(self) -> None:
        if self.fobj is None:
            self.open()
        if self.fobj is None:
            raise ValueError("Cannot read PCAP: file object is not open")

        try:
            self.reader = dpkt.pcap.Reader(self.fobj)
        except (ValueError, dpkt.dpkt.NeedData):
            self.fobj.seek(0)
            try:
                self.reader = dpkt.pcapng.Reader(self.fobj)
            except Exception:
                self.fobj.seek(0)
                self.reader = dpkt.pcap.Reader(self.fobj)

    def _packet_rows(self) -> Iterator[tuple[float, bytes]]:
        if self.reader is None:
            self._open_reader()
        assert self.reader is not None
        yield from self.reader

    def read(self, skip_empty: bool = True) -> Row:
        if self._packet_iter is None:
            self._packet_iter = self._packet_rows()
        try:
            timestamp, buf = next(self._packet_iter)
        except StopIteration:
            raise
        return {"timestamp": timestamp, "data": buf}

    def __iter__(self) -> Iterator[Row]:
        self._packet_iter = self._packet_rows()
        while True:
            try:
                yield self.read()
            except StopIteration:
                break

    def write(self, record: Row) -> None:
        raise WriteNotSupportedError("pcap", "Writing PCAP files is not yet implemented")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("pcap", "Writing PCAP files is not yet implemented")
