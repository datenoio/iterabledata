from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..helpers.utils import rowincount
from ..types import Row


class CDXIterable(BaseFileIterable):
    """
    CDX (Capture inDeX) file format reader/writer.
    CDX files are space-separated index files that point to WARC/ARC files.
    Standard CDX format fields:
    - URL
    - Timestamp
    - Original URL
    - MIME type
    - HTTP response code
    - Checksum
    - Redirect URL
    - Filename
    - Archive file offset
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
        # Standard CDX field names (CDX-11 format)
        self.keys = [
            "url",
            "timestamp",
            "original_url",
            "mime_type",
            "status_code",
            "checksum",
            "redirect",
            "filename",
            "offset",
        ]
        if "keys" in options:
            self.keys = options["keys"]
        self.pos = 0
        self.reset()

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0

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

    @staticmethod
    def id() -> str:
        return "cdx"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def read(self, skip_empty: bool = True) -> dict:
        """Read single CDX record"""
        while True:
            line = self.fobj.readline()
            if not line:
                raise StopIteration

            line = line.strip()
            if skip_empty and len(line) == 0:
                continue

            # CDX files are space-separated
            # Handle quoted fields that may contain spaces
            parts = []
            current = ""
            in_quotes = False

            for char in line:
                if char == '"':
                    in_quotes = not in_quotes
                elif char == " " and not in_quotes:
                    if current:
                        parts.append(current)
                        current = ""
                else:
                    current += char

            if current:
                parts.append(current)

            # Pad or truncate to match expected number of keys
            while len(parts) < len(self.keys):
                parts.append("")
            if len(parts) > len(self.keys):
                parts = parts[: len(self.keys)]

            result = dict(zip(self.keys, parts, strict=False))
            self.pos += 1
            return result

    def write(self, record: Row) -> None:
        """Write single CDX record"""

        # Write fields in order, space-separated
        # Quote fields that contain spaces
        def quote_field(value):
            value = str(value) if value is not None else ""
            if " " in value or value == "":
                return f'"{value}"'
            return value

        parts = [quote_field(record.get(key, "")) for key in self.keys]
        line = " ".join(parts) + "\n"
        self.fobj.write(line)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk CDX records"""
        for record in records:
            self.write(record)
