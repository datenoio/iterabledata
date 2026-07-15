from __future__ import annotations

import logging
import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..helpers.utils import rowincount
from ..types import Row

DEFAULT_ENCODING = "utf8"


class LTSVIterable(BaseFileIterable):
    """LTSV (Labeled Tab-Separated Values) format iterable"""

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str | None = None,
        options: dict[str, Any] | None = None,
    ):
        """Initialize LTSV iterable

        Args:
            filename: Path to LTSV file
            stream: File stream object
            codec: Compression codec
            mode: File mode ('r' for read, 'w' for write)
            encoding: File encoding (default: utf8)
            options: Additional options
        """
        if options is None:
            options = {}
        logging.debug(f"LTSV params: encoding: {encoding}, options {options}")

        # Determine encoding
        self.encoding = encoding
        if self.encoding is None:
            if "encoding" in options and options["encoding"] is not None:
                self.encoding = options["encoding"]
            else:
                self.encoding = DEFAULT_ENCODING

        logging.debug(f"LTSV final encoding: {self.encoding}")

        super().__init__(
            filename, stream, codec=codec, binary=False, encoding=self.encoding, mode=mode, options=options
        )

        self.pos = 0
        self.reset()

    @staticmethod
    def id() -> str:
        """Return format identifier"""
        return "ltsv"

    @staticmethod
    def is_flatonly() -> bool:
        """LTSV supports flat data only"""
        return True

    def is_streaming(self) -> bool:
        """Records are decoded incrementally; the file is not fully loaded."""
        return True

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        # Save current position
        if self.fobj is not None:
            try:
                current_pos = self.fobj.tell()
            except (AttributeError, OSError):
                current_pos = None
        else:
            current_pos = None

        # Count rows - rowincount counts newlines, but we need to count actual lines
        # If file doesn't end with newline, we need to add 1
        if self.filename:
            with open(self.filename, "rb") as f:
                content = f.read()
                # Count newlines
                newline_count = content.count(b"\n")
                # If file doesn't end with newline and has content, add 1 for the last line
                if content and not content.endswith(b"\n"):
                    newline_count += 1
                total = newline_count
        elif self.fobj is not None:
            # Use fileobj
            try:
                old_pos = self.fobj.tell()
                self.fobj.seek(0)
                content = self.fobj.read()
                newline_count = content.count(b"\n")
                if content and not content.endswith(b"\n"):
                    newline_count += 1
                total = newline_count
                self.fobj.seek(old_pos)
            except (AttributeError, OSError):
                total = rowincount(None, self.fobj)
        else:
            total = 0

        # Restore position if we had one
        if current_pos is not None and self.fobj is not None:
            try:
                self.fobj.seek(current_pos)
            except (AttributeError, OSError):
                pass

        return total

    def reset(self):
        """Reset iterator to beginning"""
        super().reset()
        self.pos = 0

    def _parse_line(self, line: str) -> dict:
        """Parse a single LTSV line into a dictionary

        Args:
            line: LTSV line string

        Returns:
            Dictionary with parsed key-value pairs
        """
        result = {}
        line = line.strip()

        if not line:
            return result

        # Split by tab to get key-value pairs
        fields = line.split("\t")

        for field in fields:
            if not field:
                continue

            # Split on first colon to get key and value
            if ":" in field:
                key, value = field.split(":", 1)
                result[key] = value
            else:
                # If no colon, treat as key with empty value
                result[field] = ""

        return result

    def _format_line(self, record: dict) -> str:
        """Format a dictionary into an LTSV line

        Args:
            record: Dictionary to format

        Returns:
            LTSV formatted line string
        """
        fields = []
        for key, value in record.items():
            # Convert value to string, handle None
            if value is None:
                value = ""
            else:
                value = str(value)
            fields.append(f"{key}:{value}")

        return "\t".join(fields) + "\n"

    def read(self, skip_empty: bool = True) -> dict:
        """Read single LTSV record

        Args:
            skip_empty: Skip empty lines

        Returns:
            Dictionary with parsed record
        """
        while True:
            line = self.fobj.readline()
            if not line:
                raise StopIteration

            line = line.rstrip("\n\r")

            if skip_empty and len(line.strip()) == 0:
                continue

            result = self._parse_line(line)
            self.pos += 1
            return result

    def write(self, record: Row) -> None:
        """Write single LTSV record

        Args:
            record: Dictionary to write
        """
        line = self._format_line(record)
        self.fobj.write(line)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk LTSV records

        Args:
            records: List of dictionaries to write
        """
        for record in records:
            self.write(record)
