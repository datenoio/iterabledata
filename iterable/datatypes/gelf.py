from __future__ import annotations

import datetime
import typing
from json import dumps, loads
from typing import Any

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..helpers.utils import rowincount
from ..types import Row


def date_handler(obj):
    return obj.isoformat() if isinstance(obj, (datetime.datetime, datetime.date)) else None


class GELIterable(BaseFileIterable):
    """
    Graylog Extended Log Format (GELF) reader/writer.
    GELF is JSON-based, one JSON object per line (similar to JSONL).
    """

    datamode = "text"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf8",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        self.pos = 0
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0

    @staticmethod
    def id() -> str:
        return "gelf"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def is_streaming(self) -> bool:
        """Records are decoded incrementally; the file is not fully loaded."""
        return True

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if self.codec is not None:
            fobj = self.codec.fileobj()
        else:
            fobj = self.fobj
        return rowincount(self.filename, fobj)

    def read(self, skip_empty: bool = True) -> dict:
        """Read single GELF record"""
        line = next(self.fobj)
        if skip_empty and len(line) == 0:
            return self.read(skip_empty)
        self.pos += 1
        if line:
            return loads(line)
        return None

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk GELF records"""
        chunk = []
        for _n in range(0, num):
            try:
                line = self.fobj.readline()
                if not line:
                    break
                chunk.append(loads(line))
                self.pos += 1
            except StopIteration:
                break
        return chunk

    def write(self, record: Row) -> None:
        """Write single GELF record"""
        # Ensure required GELF fields are present
        gelf_record = record.copy()

        # GELF v1.1 requires version field
        if "version" not in gelf_record:
            gelf_record["version"] = "1.1"

        # GELF requires timestamp (Unix timestamp)
        if "timestamp" not in gelf_record:
            import time

            gelf_record["timestamp"] = time.time()

        # GELF requires short_message or message
        if "short_message" not in gelf_record and "message" not in gelf_record:
            gelf_record["short_message"] = str(record)

        self.fobj.write(dumps(gelf_record, ensure_ascii=False, default=date_handler) + "\n")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk GELF records"""
        for record in records:
            self.write(record)
