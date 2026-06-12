from __future__ import annotations

import datetime
import typing
from json import dumps, loads
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..helpers.utils import rowincount
from ..types import Row


def date_handler(obj):
    return obj.isoformat() if isinstance(obj, (datetime.datetime, datetime.date)) else None


class JSONLDIterable(BaseFileIterable):
    """
    JSON-LD (JSON for Linking Data) format reader/writer.
    JSON-LD is a method of encoding Linked Data using JSON.
    """

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf8",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        self.pos = 0
        self.context = None
        self.data = None
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        if mode == "r":
            self.reset()
        pass

    def reset(self):
        """Reset iterable and reload data"""
        super().reset()
        self.pos = 0
        self.line_mode = False

        # Try to detect format: line-by-line (JSONL-like) or full document
        # Read first few lines to check
        current_pos = self.fobj.tell()
        first_line = self.fobj.readline()
        if not first_line.strip():
            # Empty file
            self.data = []
            self.total = 0
            return

        first_line_stripped = first_line.strip()

        # Check if first line is a complete JSON object (starts with {)
        if first_line_stripped.startswith("{"):
            try:
                # Try to parse first line as JSON
                loads(first_line_stripped)
                # Check if there's a second line (indicates line-by-line format)
                second_line = self.fobj.readline()
                self.fobj.seek(current_pos)
                if second_line.strip() and second_line.strip().startswith("{"):
                    # Multiple lines starting with {, treat as line-by-line format
                    self.line_mode = True
                    self.data = None  # Will read line by line
                    self.total = None  # Will count as we go
                    return
            except Exception:
                pass

        # Full document format - read entire file
        self.fobj.seek(current_pos)
        content = self.fobj.read()
        if isinstance(content, bytes):
            content = content.decode(self.encoding)

        try:
            self.data = loads(content)
        except Exception:
            # If parsing fails, might be line-by-line format
            # Try reading line by line
            self.fobj.seek(current_pos)
            self.line_mode = True
            self.data = None
            self.total = None
            return

        # Handle different JSON-LD document structures
        if isinstance(self.data, dict):
            # Check if it's a JSON-LD document with @graph
            if "@graph" in self.data:
                # Extract context if present
                if "@context" in self.data:
                    self.context = self.data["@context"]
                self.data = self.data["@graph"]
                self.total = len(self.data) if isinstance(self.data, list) else 1
            else:
                # Single JSON-LD object
                self.data = [self.data]
                self.total = 1
        elif isinstance(self.data, list):
            # Array of JSON-LD objects
            self.total = len(self.data)
        else:
            # Unexpected format
            self.data = [self.data]
            self.total = 1

    @staticmethod
    def id() -> str:
        return "jsonld"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if self.line_mode:
            # For line-by-line format, count lines
            if self.codec is not None:
                fobj = self.codec.fileobj()
            else:
                fobj = self.fobj
            return rowincount(self.filename, fobj)

        if self.data is not None and self.total is not None:
            return self.total
        # If data not loaded yet, try to count
        if self.codec is not None:
            fobj = self.codec.fileobj()
        else:
            fobj = self.fobj
        # For JSON-LD, we need to parse to count accurately
        # This is a fallback that counts lines (not accurate for all cases)
        return rowincount(self.filename, fobj)

    def read(self, skip_empty: bool = True) -> dict:
        """Read single JSON-LD record"""
        if self.line_mode:
            # Line-by-line format (like JSONL)
            line = self.fobj.readline()
            if not line:
                raise StopIteration
            if skip_empty and len(line.strip()) == 0:
                return self.read(skip_empty)
            self.pos += 1
            row = loads(line.strip())
            return row

        # Full document format
        if self.data is None:
            self.reset()

        if self.total is not None and self.pos >= self.total:
            raise StopIteration

        row = self.data[self.pos]
        self.pos += 1

        # Add context back if it was extracted
        if self.context and isinstance(row, dict) and "@context" not in row:
            row = row.copy()
            row["@context"] = self.context

        return row

    def write(self, record: Row) -> None:
        """Write single JSON-LD record"""
        # If this is the first write, initialize context if present
        if self.pos == 0 and isinstance(record, dict) and "@context" in record:
            self.context = record.get("@context")

        # Write as a single JSON-LD object (one per line, similar to JSONL)
        # This allows streaming large datasets
        json_str = dumps(record, ensure_ascii=False, default=date_handler)
        self.fobj.write(json_str + "\n")
        self.pos += 1

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk JSON-LD records"""
        for record in records:
            self.write(record)
