# from bson import BSON
from __future__ import annotations

import typing
from typing import Any

import bson

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..types import Row


class BSONIterable(BaseFileIterable):
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
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.reset()
        pass

    def reset(self):
        super().reset()
        self.reader = bson.decode_file_iter(self.fobj)

    @staticmethod
    def id() -> str:
        return "bson"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def is_streaming(self) -> bool:
        """Records are decoded incrementally; the file is not fully loaded."""
        return True

    def read(self, skip_empty: bool = True) -> dict:
        """Read single BSON record"""
        return next(self.reader)

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk bson record"""
        chunk = []
        for _n in range(0, num):
            try:
                chunk.append(next(self.reader))
            except StopIteration:
                break
        return chunk

    def write(self, record: Row) -> None:
        """Write single bson record"""
        self.fobj.write(bson.BSON.encode(record))

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk bson record"""
        for record in records:
            self.fobj.write(bson.BSON.encode(record))
