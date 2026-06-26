from __future__ import annotations

import json
import re
import typing
from typing import Any

import avro.schema
from avro.datafile import DataFileReader, DataFileWriter
from avro.io import DatumReader, DatumWriter

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..types import Row

# Avro names must start with [A-Za-z_] and contain only [A-Za-z0-9_] afterwards.
_AVRO_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Default Avro codec. ``deflate`` is part of the Avro spec and needs no extra
# dependency (unlike ``snappy``/``zstandard``).
_DEFAULT_AVRO_CODEC = "deflate"


def fields_to_avro_schema(fields: list[str], name: str = "Record", namespace: str = "iterable.avro") -> dict:
    """Build an Avro record schema (all nullable string fields) from field names.

    Every field is typed as ``["null", "string"]`` so that missing/``None``
    values are representable and heterogeneous source values can be coerced to
    strings, mirroring the string-based schema used by the ORC writer.
    """
    invalid = [f for f in fields if not _AVRO_NAME_RE.match(str(f))]
    if invalid:
        raise ValueError(
            "Cannot write Avro: field names must match [A-Za-z_][A-Za-z0-9_]* "
            f"(invalid names: {invalid}). Rename/sanitize these columns, or use a "
            "format with fewer naming restrictions (e.g. parquet, orc, jsonl)."
        )
    return {
        "namespace": namespace,
        "type": "record",
        "name": name,
        "fields": [{"name": str(f), "type": ["null", "string"], "default": None} for f in fields],
    }


class AVROIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode="r",
        keys: list[str] | None = None,
        schema: dict | str | None = None,
        compression: str | None = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        self.keys = keys
        self.schema = schema
        # Accept compression via explicit arg or options ("compression"/"codec").
        self.compression = compression or options.get("compression") or options.get("codec") or _DEFAULT_AVRO_CODEC
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        self.cursor = None
        self.writer = None
        # Defer writer creation until the first record is written so the schema
        # can be inferred from the data when no schema/keys were supplied. This
        # mirrors the ORC writer and avoids requiring callers to pass ``keys``.
        self._writer_pending = False
        if self.mode == "r":
            self.cursor = DataFileReader(self.fobj, DatumReader())
        elif self.mode == "w":
            if self.schema is not None or self.keys is not None:
                self._create_writer()
            else:
                self._writer_pending = True

    def _create_writer(self) -> None:
        """Create the underlying Avro writer from the configured schema/keys."""
        if self.schema is not None:
            schema_obj = self.schema if isinstance(self.schema, str) else json.dumps(self.schema)
        else:
            schema_obj = json.dumps(fields_to_avro_schema(self.keys))
        parsed = avro.schema.parse(schema_obj)
        self.writer = DataFileWriter(self.fobj, DatumWriter(), parsed, codec=self.compression)
        self._writer_pending = False

    def _ensure_writer(self, record: Row) -> None:
        """Lazily create the writer, inferring field names from the first record."""
        if self._writer_pending:
            self.keys = list(record.keys())
            self._create_writer()

    def _coerce(self, record: Row) -> dict:
        """Coerce a record to the all-nullable-string schema.

        Ensures every schema field is present and non-``None`` values are
        stringified so Avro's ``["null", "string"]`` typing always validates.
        """
        out: dict[str, Any] = {}
        for k in self.keys:
            v = record.get(k)
            out[str(k)] = None if v is None else str(v)
        return out

    @staticmethod
    def id() -> str:
        return "avro"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def close(self):
        """Close iterable"""
        if self.writer is not None:
            self.writer.close()
        super().close()

    def read(self, skip_empty: bool = True) -> dict:
        """Read single record"""
        row = next(self.cursor)
        self.pos += 1
        return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read a bulk of Avro records."""
        chunk = []
        for _n in range(num):
            try:
                chunk.append(next(self.cursor))
                self.pos += 1
            except StopIteration:
                break
        return chunk

    def write(self, record: Row) -> None:
        """Write single record"""
        self._ensure_writer(record)
        self.writer.append(self._coerce(record))

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk records"""
        if not records:
            return
        self._ensure_writer(records[0])
        for record in records:
            self.writer.append(self._coerce(record))
