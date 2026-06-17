from __future__ import annotations

import datetime
import pickle
import typing
from typing import Any

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..types import Row


def date_handler(obj):
    return obj.isoformat() if isinstance(obj, (datetime.datetime, datetime.date)) else None


class PickleIterable(BaseFileIterable):
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
        self.pos = 0
        pass

    @staticmethod
    def id() -> str:
        return "pickle"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single record"""
        try:
            return pickle.load(self.fobj)
        except EOFError:
            raise StopIteration from None

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk records"""
        chunk: list[dict] = []
        for _ in range(num):
            try:
                chunk.append(pickle.load(self.fobj))
            except EOFError:
                break
        return chunk

    def write(self, record: Row) -> None:
        """Write single record into file"""
        pickle.dump(record, self.fobj)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk records"""
        for record in records:
            pickle.dump(record, self.fobj)
