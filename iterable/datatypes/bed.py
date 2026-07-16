"""Streaming BED3-BED12+ interval reader and writer."""

from __future__ import annotations

import typing
from typing import Any

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..types import Row

BED_FIELDS = (
    "chrom",
    "start",
    "end",
    "name",
    "score",
    "strand",
    "thick_start",
    "thick_end",
    "item_rgb",
    "block_count",
    "block_sizes",
    "block_starts",
)


class BEDIterable(BaseFileIterable):
    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        headers: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ):
        self.headers = list(headers or [])
        super().__init__(filename, stream, codec=codec, mode=mode, binary=False, encoding="utf8", options=options or {})
        self.reset()

    @staticmethod
    def id() -> str:
        return "bed"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        self._line_number = 0

    @staticmethod
    def _parse_values(values: list[str]) -> Row:
        if len(values) < 3:
            raise ValueError("BED requires at least chrom, start, and end")
        row: Row = {BED_FIELDS[0]: values[0], BED_FIELDS[1]: int(values[1]), BED_FIELDS[2]: int(values[2])}
        if row["start"] < 0 or row["end"] < row["start"]:
            raise ValueError("BED coordinates must be 0-based with end >= start")
        for index, value in enumerate(values[3:12], start=3):
            key = BED_FIELDS[index]
            if key in {"score", "thick_start", "thick_end", "block_count"}:
                row[key] = int(value) if value not in {".", ""} else None
            elif key in {"block_sizes", "block_starts"}:
                row[key] = [int(item) for item in value.rstrip(",").split(",") if item]
            else:
                row[key] = value
        if len(values) > 12:
            row["extra"] = values[12:]
        if row.get("block_count") is not None:
            sizes = len(row.get("block_sizes", []))
            starts = len(row.get("block_starts", []))
            if sizes != row["block_count"] or starts != row["block_count"]:
                raise ValueError("BED block_count does not match block_sizes/block_starts")
        return row

    def read(self, skip_empty: bool = True) -> Row:
        while True:
            line = self.fobj.readline()
            if not line:
                raise StopIteration
            self._line_number += 1
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(("#", "track", "browser")):
                self.headers.append(stripped)
                continue
            row = self._parse_values(stripped.split("\t"))
            self.pos += 1
            return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[Row]:
        rows: list[Row] = []
        for _ in range(num):
            try:
                rows.append(self.read())
            except StopIteration:
                break
        return rows

    @staticmethod
    def _format_value(key: str, value: Any) -> str:
        if value is None:
            return "."
        if key in {"block_sizes", "block_starts"}:
            return ",".join(str(item) for item in value) + ","
        return str(value)

    def write(self, record: Row) -> None:
        self.write_bulk([record])

    def write_bulk(self, records: list[Row]) -> None:
        for record in records:
            values = [self._format_value(key, record.get(key)) for key in BED_FIELDS if key in record]
            if len(values) < 3:
                raise ValueError("BED writes require chrom, start, and end")
            self.fobj.write("\t".join(values) + "\n")
