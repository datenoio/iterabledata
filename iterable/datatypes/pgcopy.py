from __future__ import annotations

import csv
import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class PGCopyIterable(BaseFileIterable):
    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf8",
        delimiter: str = "\t",
        null: str = "\\N",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        self.delimiter = delimiter
        self.null = null
        if "delimiter" in options:
            self.delimiter = options["delimiter"]
        if "null" in options:
            self.null = options["null"]
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            # PostgreSQL COPY format is tab-delimited by default
            # Skip header if present (starts with column names)
            # Format: col1\tcol2\tcol3\n
            self.reader = csv.DictReader(self.fobj, delimiter=self.delimiter)
            # Try to detect if first line is header
            self.fobj.seek(0)
            first_line = self.fobj.readline()
            self.fobj.seek(0)

            # Check if first line looks like header (no tabs with numbers/quotes)
            if not any(char.isdigit() for char in first_line) and self.delimiter in first_line:
                # Likely a header
                self.reader = csv.DictReader(self.fobj, delimiter=self.delimiter)
            else:
                # No header, use generic column names
                self.reader = csv.reader(self.fobj, delimiter=self.delimiter)
                self.has_header = False
        else:
            self.writer = None
            self.keys = None

    @staticmethod
    def id() -> str:
        return "pgcopy"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def read(self, skip_empty: bool = True) -> dict:
        """Read single PostgreSQL COPY record"""
        if hasattr(self, "has_header") and not self.has_header:
            row = next(self.reader)
            # Convert to dict with generic column names
            result = {}
            for idx, value in enumerate(row):
                if value == self.null:
                    value = None
                result[f"col_{idx}"] = value
            self.pos += 1
            return result
        else:
            row = next(self.reader)
            # Convert NULL values
            for key, value in row.items():
                if value == self.null:
                    row[key] = None
            self.pos += 1
            return row

    def write(self, record: Row) -> None:
        """Write single PostgreSQL COPY record"""
        if self.writer is None:
            # Initialize writer on first write
            self.keys = list(record.keys())
            self.writer = csv.DictWriter(self.fobj, fieldnames=self.keys, delimiter=self.delimiter, lineterminator="\n")
            # Write header
            header_row = {k: k for k in self.keys}
            self.writer.writerow(header_row)

        # Convert None to NULL marker
        row = {}
        for key in self.keys:
            value = record.get(key)
            if value is None:
                row[key] = self.null
            else:
                row[key] = str(value)

        self.writer.writerow(row)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk PostgreSQL COPY records"""
        if not records:
            return

        if self.writer is None:
            # Initialize writer
            self.keys = list(records[0].keys())
            self.writer = csv.DictWriter(self.fobj, fieldnames=self.keys, delimiter=self.delimiter, lineterminator="\n")
            # Write header
            header_row = {k: k for k in self.keys}
            self.writer.writerow(header_row)

        # Write all records
        for record in records:
            row = {}
            for key in self.keys:
                value = record.get(key)
                if value is None:
                    row[key] = self.null
                else:
                    row[key] = str(value)
            self.writer.writerow(row)
