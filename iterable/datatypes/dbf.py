from __future__ import annotations

import typing
from typing import Any

from dbfread import DBF

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..exceptions import ReadError


class DBFIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode="r",
        encoding: str = "utf-8",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, noopen=True, options=options)
        self.encoding = encoding
        if "encoding" in options:
            self.encoding = options["encoding"]
        self.reset()
        pass

    def reset(self):
        """Reopen file and open DBF table"""
        super().reset()
        if self.filename is None:
            raise ReadError(
                "DBF requires a file path; stream and codec are not supported.",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        # DBF files need to be opened directly using filename
        self.table = DBF(self.filename, encoding=self.encoding)
        self.iterator = iter(self.table)

    @staticmethod
    def id() -> str:
        """ID of the data source type"""
        return "dbf"

    @staticmethod
    def is_flatonly() -> bool:
        """Flag that data is flat"""
        return True

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        return len(self.table)

    def read(self, skip_empty: bool = True) -> dict:
        """Read single DBF record"""
        try:
            record = next(self.iterator)
            # Convert OrderedDict to regular dict
            return dict(record)
        except StopIteration:
            raise StopIteration from None

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk DBF records"""
        chunk = []
        for _n in range(0, num):
            try:
                record = next(self.iterator)
                # Convert OrderedDict to regular dict
                chunk.append(dict(record))
            except StopIteration:
                break
        return chunk
