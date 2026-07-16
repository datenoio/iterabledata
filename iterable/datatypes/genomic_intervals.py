"""Streaming GFF3 and GTF interval profiles."""

from __future__ import annotations

import re
import typing
from collections import OrderedDict
from typing import Any

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..types import Row

_GTF_ATTR = re.compile(r"\s*([^\s]+)\s+\"([^\"]*)\"\s*;?")


class _GenomicIntervalIterable(BaseFileIterable):
    format_name = "gff3"
    coordinate_convention = "1-based, closed"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        attribute_mode: str = "parsed",
        include_comments: bool = False,
        options: dict[str, Any] | None = None,
    ):
        if attribute_mode not in {"parsed", "lossless"}:
            raise ValueError("attribute_mode must be 'parsed' or 'lossless'")
        self.attribute_mode = attribute_mode
        self.include_comments = include_comments
        self.metadata: list[str] = []
        super().__init__(filename, stream, codec=codec, mode=mode, binary=False, encoding="utf8", options=options or {})
        self.reset()

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        self.metadata = []

    def _parse_attributes(self, raw: str) -> OrderedDict[str, str]:
        attributes: OrderedDict[str, str] = OrderedDict()
        if raw in {".", ""}:
            return attributes
        if self.format_name == "gtf":
            for match in _GTF_ATTR.finditer(raw):
                attributes[match.group(1)] = match.group(2)
            return attributes
        for part in raw.split(";"):
            if not part:
                continue
            key, separator, value = part.partition("=")
            if not separator:
                raise ValueError(f"Malformed GFF3 attribute {part!r}")
            attributes[key] = value
        return attributes

    def read(self, skip_empty: bool = True) -> Row:
        while True:
            line = self.fobj.readline()
            if not line:
                raise StopIteration
            stripped = line.rstrip("\r\n")
            if not stripped:
                continue
            if stripped.startswith("#"):
                self.metadata.append(stripped)
                if self.include_comments:
                    return {"record_type": "directive", "value": stripped}
                continue
            fields = stripped.split("\t")
            if len(fields) != 9:
                raise ValueError(f"{self.format_name.upper()} records require nine tab-separated columns")
            try:
                start, end = int(fields[3]), int(fields[4])
            except ValueError as exc:
                raise ValueError(f"Invalid {self.format_name.upper()} coordinates") from exc
            if start < 1 or end < start:
                raise ValueError(f"{self.format_name.upper()} coordinates are {self.coordinate_convention}")
            attributes_raw = fields[8]
            row: Row = {
                "seqid": fields[0],
                "source": fields[1],
                "type": fields[2],
                "start": start,
                "end": end,
                "score": None if fields[5] == "." else fields[5],
                "strand": fields[6],
                "phase": None if fields[7] == "." else fields[7],
                "attributes": self._parse_attributes(attributes_raw),
            }
            if self.attribute_mode == "lossless":
                row["attributes_raw"] = attributes_raw
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

    def write(self, record: Row) -> None:
        self.write_bulk([record])

    def write_bulk(self, records: list[Row]) -> None:
        for record in records:
            attributes = record.get("attributes_raw") if self.attribute_mode == "lossless" else None
            if attributes is None:
                values = record.get("attributes", {})
                if self.format_name == "gtf":
                    attributes = "".join(
                        f'{key} "{str(value).replace(chr(34), chr(39))}"; ' for key, value in values.items()
                    ).rstrip()
                else:
                    attributes = ";".join(f"{key}={value}" for key, value in values.items()) or "."
            fields = [
                record.get("seqid", "."),
                record.get("source", "."),
                record.get("type", "."),
                record["start"],
                record["end"],
                record.get("score") if record.get("score") is not None else ".",
                record.get("strand", "."),
                record.get("phase") if record.get("phase") is not None else ".",
                attributes,
            ]
            self.fobj.write("\t".join(map(str, fields)) + "\n")


class GFF3Iterable(_GenomicIntervalIterable):
    format_name = "gff3"

    @staticmethod
    def id() -> str:
        return "gff3"


class GTFIterable(_GenomicIntervalIterable):
    format_name = "gtf"

    @staticmethod
    def id() -> str:
        return "gtf"
