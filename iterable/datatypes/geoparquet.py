"""GeoParquet profile over the streaming Parquet implementation."""

from __future__ import annotations

import json
from typing import Any

import pyarrow

from .parquet import ParquetIterable


class GeoParquetIterable(ParquetIterable):
    """Parquet rows with GeoParquet metadata and raw WKB geometry by default."""

    @staticmethod
    def id() -> str:
        return "geoparquet"

    def __init__(self, *args: Any, geometry_column: str = "geometry", crs: Any = None, **kwargs: Any):
        self.geometry_column = geometry_column
        self.geo_crs = crs
        self.geo_metadata: dict[str, Any] = {}
        super().__init__(*args, **kwargs)

    def reset(self) -> None:
        super().reset()
        if self.reader is not None:
            metadata = self.reader.schema_arrow.metadata or {}
            raw = metadata.get(b"geo")
            if raw:
                try:
                    self.geo_metadata = json.loads(raw.decode("utf-8"))
                except (TypeError, ValueError, UnicodeDecodeError):
                    self.geo_metadata = {}

    def _geo_schema_metadata(self, metadata: dict[bytes, bytes] | None = None) -> dict[bytes, bytes]:
        result = dict(metadata or {})
        geo = dict(self.geo_metadata)
        geo.setdefault("version", "1.0.0")
        geo.setdefault("primary_column", self.geometry_column)
        geo.setdefault("columns", {})
        geo["columns"].setdefault(self.geometry_column, {"encoding": "WKB", "geometry_types": []})
        if self.geo_crs is not None:
            geo["columns"][self.geometry_column]["crs"] = self.geo_crs
        result[b"geo"] = json.dumps(geo, separators=(",", ":")).encode("utf-8")
        return result

    def _write_records(self, records: list[dict[str, Any]]) -> None:
        records = self._prepare_records(records)
        if self.writer is None:
            table = pyarrow.Table.from_pylist(records)
            table = table.replace_schema_metadata(self._geo_schema_metadata(table.schema.metadata))
            self.writer = pyarrow.parquet.ParquetWriter(
                self.fobj, table.schema, compression=self.compression, use_dictionary=False
            )
        else:
            normalized = self._normalize_records_to_schema(records, self.writer.schema)
            table = pyarrow.Table.from_pylist(normalized, schema=self.writer.schema)
        self.writer.write_table(table)
