"""GeoParquet profile over the streaming Parquet implementation."""

from __future__ import annotations

from typing import Any

import pyarrow

from ..base import DEFAULT_BULK_NUMBER
from ..exceptions import FormatParseError
from ..helpers.geo import (
    DEFAULT_GEOMETRY_COLUMN,
    build_geo_metadata,
    dumps_geo_metadata,
    feature_row_from_wkb,
    geo_column_metadata,
    parse_geo_metadata,
)
from ..types import Row
from .parquet import ParquetIterable

GEOMETRY_MODES = ("wkb", "feature")


class GeoParquetIterable(ParquetIterable):
    """Parquet rows with GeoParquet metadata and raw WKB geometry by default.

    Row modes:
    - ``geometry_mode="wkb"`` (default): rows pass through unchanged; the
      geometry column stays raw WKB bytes and batch/projection reading is
      untouched.
    - ``geometry_mode="feature"``: the primary geometry column is decoded to a
      GeoJSON-like mapping (requires Shapely) and rows take the shared feature
      shape ``{"geometry": ..., **properties}``.

    GeoParquet metadata stays available through ``geo_metadata`` and the
    ``primary_geometry_column``, ``crs``, ``geometry_encoding``,
    ``geometry_types`` and ``bbox`` accessors.
    """

    @staticmethod
    def id() -> str:
        return "geoparquet"

    def __init__(
        self,
        *args: Any,
        geometry_column: str = DEFAULT_GEOMETRY_COLUMN,
        crs: Any = None,
        geometry_mode: str = "wkb",
        encoding: str = "WKB",
        geometry_types: list[str] | None = None,
        bbox: list[float] | tuple[float, ...] | None = None,
        geometry_columns: dict[str, dict[str, Any]] | None = None,
        validate_metadata: bool = True,
        **kwargs: Any,
    ):
        if geometry_mode not in GEOMETRY_MODES:
            raise ValueError(f"geometry_mode must be one of {GEOMETRY_MODES}, got {geometry_mode!r}")
        self.geometry_column = geometry_column
        self.geo_crs = crs
        self.geometry_mode = geometry_mode
        self.geo_encoding = encoding
        self.geo_geometry_types = geometry_types
        self.geo_bbox = bbox
        self.geo_columns = geometry_columns
        self.validate_metadata = validate_metadata
        self.geo_metadata: dict[str, Any] = {}
        super().__init__(*args, **kwargs)

    def reset(self) -> None:
        super().reset()
        self.geo_metadata = {}
        if self.mode == "r" and self.reader is not None:
            metadata = self.reader.schema_arrow.metadata or {}
            self.geo_metadata = parse_geo_metadata(metadata.get(b"geo"))
            if self.validate_metadata and not self.geo_metadata:
                raise FormatParseError(
                    format_id="geoparquet",
                    message=(
                        "File has no valid GeoParquet 'geo' metadata. Open it as plain Parquet "
                        "(format='parquet') or pass validate_metadata=False to read it anyway."
                    ),
                    filename=getattr(self, "filename", None),
                )

    # -- GeoParquet metadata accessors -------------------------------------

    @property
    def primary_geometry_column(self) -> str:
        """Primary geometry column from the ``geo`` metadata (falls back to the configured column)."""
        return self.geo_metadata.get("primary_column", self.geometry_column)

    def _column_metadata(self, column: str | None = None) -> dict[str, Any]:
        return geo_column_metadata(self.geo_metadata, column)

    def crs(self, column: str | None = None) -> Any:
        """CRS recorded for the geometry column, or the CRS configured for writes."""
        return self._column_metadata(column).get("crs", self.geo_crs)

    def geometry_encoding(self, column: str | None = None) -> str | None:
        """Geometry encoding declared for the column (e.g. ``WKB``).

        Named ``geometry_encoding`` because ``BaseFileIterable.encoding`` is
        the text-encoding attribute.
        """
        return self._column_metadata(column).get("encoding", self.geo_encoding)

    def geometry_types(self, column: str | None = None) -> list[str]:
        """Geometry types declared for the column."""
        types = self._column_metadata(column).get("geometry_types")
        return list(types) if isinstance(types, list) else []

    def bbox(self, column: str | None = None) -> list[float] | None:
        """Bounding box declared for the column, if any."""
        box = self._column_metadata(column).get("bbox")
        return list(box) if isinstance(box, (list, tuple)) else None

    # -- Row conversion -----------------------------------------------------

    def _convert_row(self, row: Row) -> Row:
        if self.geometry_mode == "wkb":
            return row
        return feature_row_from_wkb(row, self.primary_geometry_column)

    def read(self, skip_empty: bool = True) -> Row:
        return self._convert_row(super().read(skip_empty=skip_empty))

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[Row]:
        rows = super().read_bulk(num)
        if self.geometry_mode == "wkb":
            return rows
        return [self._convert_row(row) for row in rows]

    # -- Writes -------------------------------------------------------------

    def _geo_schema_metadata(self, metadata: dict[bytes, bytes] | None = None) -> dict[bytes, bytes]:
        result = dict(metadata or {})
        try:
            geo = build_geo_metadata(
                primary_column=self.geometry_column,
                crs=self.geo_crs,
                encoding=self.geo_encoding,
                geometry_types=self.geo_geometry_types,
                bbox=self.geo_bbox,
                columns=self.geo_columns,
                existing=self.geo_metadata,
            )
            result[b"geo"] = dumps_geo_metadata(geo)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid GeoParquet metadata configuration: {exc}") from exc
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
