from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..helpers.utils import rowincount
from ..types import Row

DEFAULT_ENCODING = "utf8"


class FixedWidthIterable(BaseFileIterable):
    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        widths: list[int] = None,
        names: list[str] = None,
        encoding: str | None = None,
        mode: str = "r",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        self.widths = widths
        self.names = names
        self.encoding = encoding or DEFAULT_ENCODING

        if "widths" in options:
            self.widths = options["widths"]
        if "names" in options:
            self.names = options["names"]
        if "encoding" in options:
            self.encoding = options["encoding"]

        super().__init__(
            filename, stream, codec=codec, binary=False, mode=mode, encoding=self.encoding, options=options
        )
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            if self.widths is None or self.names is None:
                raise ValueError("Fixed-width files require 'widths' and 'names' parameters")
            if len(self.widths) != len(self.names):
                raise ValueError("Length of 'widths' must match length of 'names'")

    @staticmethod
    def id() -> str:
        return "fwf"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        return rowincount(self.filename, self.fobj)

    def read(self, skip_empty: bool = True) -> dict:
        """Read single fixed-width record"""
        line = self.fobj.readline()
        if not line:
            raise StopIteration
        if skip_empty and len(line.strip()) == 0:
            return self.read(skip_empty)

        self.pos += 1
        record = {}
        start = 0
        for _i, (name, width) in enumerate(zip(self.names, self.widths, strict=False)):
            end = start + width
            value = line[start:end].strip()
            record[name] = value
            start = end
        return record

    def write(self, record: Row) -> None:
        """Write single fixed-width record"""
        if self.widths is None or self.names is None:
            raise ValueError("Fixed-width files require 'widths' and 'names' parameters")

        line_parts = []
        for name, width in zip(self.names, self.widths, strict=False):
            value = str(record.get(name, ""))
            # Pad or truncate to fit width
            formatted = value[:width].ljust(width)
            line_parts.append(formatted)

        self.fobj.write("".join(line_parts) + "\n")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk fixed-width records"""
        for record in records:
            self.write(record)
