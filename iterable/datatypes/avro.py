from __future__ import annotations

import typing
from typing import Any

from avro.datafile import DataFileReader
from avro.io import DatumReader

from ..base import BaseCodec, BaseFileIterable


class AVROIterable(BaseFileIterable):
    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode="r",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        self.cursor = DataFileReader(self.fobj, DatumReader())

    @staticmethod
    def id() -> str:
        return "avro"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def read(self, skip_empty: bool = True) -> dict:
        """Read single record"""
        row = next(self.cursor)
        self.pos += 1
        return row
