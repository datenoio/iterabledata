"""Minimal ``.journal`` format: one ``key=value;key=value`` record per line.

Deliberately tiny: it exists to demonstrate the IterableData plugin contract
(entry-point discovery + the BaseFileIterable subclass API), not to be a
production format.
"""

from __future__ import annotations

import typing
from typing import Any

from iterable.base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable


class JournalIterable(BaseFileIterable):
    """Read and write ``.journal`` files (``k=v;k=v`` lines)."""

    datamode = "text"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        keys: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        super().__init__(filename, stream, codec=codec, mode=mode, options=options)
        self.keys = keys
        self.reset()

    @staticmethod
    def id() -> str:
        return "journal"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    def reset(self) -> None:
        super().reset()
        self.pos = 0

    @staticmethod
    def _parse_line(line: str) -> dict:
        record = {}
        for pair in line.strip().split(";"):
            if not pair or "=" not in pair:
                continue
            key, _, value = pair.partition("=")
            record[key.strip()] = value.strip()
        return record

    @staticmethod
    def _format_line(record: dict) -> str:
        return ";".join(f"{key}={value}" for key, value in record.items())

    def read(self, skip_empty: bool = True) -> dict:
        """Read a single journal record."""
        while True:
            line = self.fobj.readline()
            if line == "":
                raise StopIteration
            record = self._parse_line(line)
            if record or not skip_empty:
                self.pos += 1
                return record

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read up to ``num`` journal records."""
        chunk = []
        for _ in range(num):
            try:
                chunk.append(self.read())
            except StopIteration:
                break
        return chunk

    def write(self, record: dict) -> None:
        """Write a single journal record."""
        if self._validation_hooks:
            validated = self._apply_validation_hooks(record)
            if validated is None:  # Skipped
                return
            record = validated
        self.fobj.write(self._format_line(record) + "\n")

    def write_bulk(self, records: list[dict]) -> None:
        """Write journal records in bulk."""
        if records is None:
            raise TypeError("write_bulk() requires a list of records, got None")
        if self._validation_hooks:
            validated_records = []
            for record in records:
                validated = self._apply_validation_hooks(record)
                if validated is not None:  # Not skipped
                    validated_records.append(validated)
            records = validated_records
        for record in records:
            self.write(record)
