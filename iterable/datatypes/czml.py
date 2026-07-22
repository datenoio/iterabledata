"""Cesium CZML packet iterable (JSON documents)."""

from __future__ import annotations

import json
import typing
from typing import Any

try:
    import ijson

    HAS_IJSON = True
except ImportError:
    HAS_IJSON = False

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..types import Row


class CZMLIterable(BaseFileIterable):
    """Read/write Cesium CZML documents as an iterable of packet dicts.

    Accepts a JSON array of packets or a single packet object. When the file
    starts with ``[``, uses ``ijson`` for streaming if available, otherwise
    ``json.load``.
    """

    datamode = "text"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf-8",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        self._streaming = False
        self._parser = None
        self._items_buffer: list[Row] = []
        self._packets: list[Row] = []
        self._iterator: typing.Iterator[Row] | None = None
        self._write_started = False
        self._first_write = True
        super().__init__(
            filename,
            stream,
            codec=codec,
            binary=False,
            mode=mode,
            encoding=encoding,
            options=options,
        )
        self.reset()

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        self._streaming = False
        self._parser = None
        self._items_buffer = []
        self._packets = []
        self._iterator = None
        self._write_started = False
        self._first_write = True

        if self.mode in ("w", "wr"):
            if hasattr(self.fobj, "seek") and hasattr(self.fobj, "truncate"):
                try:
                    self.fobj.seek(0)
                    self.fobj.truncate(0)
                except Exception:
                    pass
            self.fobj.write("[")
            self._write_started = True
            return

        # Peek first non-whitespace character
        if hasattr(self.fobj, "seek"):
            self.fobj.seek(0)
        first = self._peek_first_char()
        if first == "[" and HAS_IJSON:
            self._streaming = True
            if hasattr(self.fobj, "seek"):
                self.fobj.seek(0)
            self._parser = ijson.items(self.fobj, "item")
            try:
                first_item = next(self._parser)
                self._items_buffer = [first_item]
            except StopIteration:
                self._items_buffer = []
        else:
            if hasattr(self.fobj, "seek"):
                self.fobj.seek(0)
            data = json.load(self.fobj)
            if isinstance(data, list):
                self._packets = data
            elif isinstance(data, dict):
                self._packets = [data]
            else:
                raise ValueError("CZML document must be a JSON array or object")
            self._iterator = iter(self._packets)

    def _peek_first_char(self) -> str | None:
        while True:
            ch = self.fobj.read(1)
            if not ch:
                return None
            if not ch.isspace():
                return ch

    @staticmethod
    def id() -> str:
        return "czml"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def is_streaming(self) -> bool:
        return self._streaming

    def read(self, skip_empty: bool = True) -> Row:
        if self._streaming:
            if self._items_buffer:
                item = self._items_buffer.pop(0)
                self.pos += 1
                return item
            item = next(self._parser)
            self.pos += 1
            return item
        assert self._iterator is not None
        item = next(self._iterator)
        self.pos += 1
        return item

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[Row]:
        rows: list[Row] = []
        for _ in range(num):
            try:
                rows.append(self.read())
            except StopIteration:
                break
        return rows

    def write(self, record: Row) -> None:
        if not self._write_started:
            self.fobj.write("[")
            self._write_started = True
            self._first_write = True
        if not self._first_write:
            self.fobj.write(",")
        self._first_write = False
        json.dump(record, self.fobj, ensure_ascii=False)
        self.pos += 1

    def write_bulk(self, records: list[Row]) -> None:
        for record in records:
            self.write(record)

    def close(self) -> None:
        if self.mode in ("w", "wr") and self._write_started:
            try:
                self.fobj.write("]")
            except Exception:
                pass
        super().close()
