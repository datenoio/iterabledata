"""Shared geospatial metadata and geometry helpers.

These helpers are deliberately free of file-backend dependencies: they operate
on GeoParquet ``geo`` metadata payloads and WKB geometry bytes only, so they
can be tested without Parquet or FlatGeobuf files.
"""

from __future__ import annotations

import json
from typing import Any

DEFAULT_GEO_VERSION = "1.0.0"
DEFAULT_GEOMETRY_COLUMN = "geometry"
DEFAULT_GEOMETRY_ENCODING = "WKB"


def parse_geo_metadata(raw: bytes | str | None) -> dict[str, Any]:
    """Parse a GeoParquet ``geo`` metadata payload.

    Returns an empty dict when the payload is missing, undecodable, or not a
    JSON object. Never raises; callers that require valid metadata must check
    for an empty result themselves.
    """
    if raw is None:
        return {}
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError:
            return {}
    if not isinstance(raw, str):
        return {}
    try:
        parsed = json.loads(raw)
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def build_geo_metadata(
    primary_column: str = DEFAULT_GEOMETRY_COLUMN,
    crs: Any = None,
    encoding: str = DEFAULT_GEOMETRY_ENCODING,
    geometry_types: list[str] | None = None,
    bbox: list[float] | tuple[float, ...] | None = None,
    columns: dict[str, dict[str, Any]] | None = None,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a GeoParquet ``geo`` metadata object.

    Unknown fields from ``existing`` are preserved. The primary column always
    ends up with an entry under ``columns``; additional geometry columns can be
    declared through ``columns`` (each value must be a dict).
    """
    geo: dict[str, Any] = dict(existing or {})
    geo.setdefault("version", DEFAULT_GEO_VERSION)
    geo["primary_column"] = primary_column

    declared: dict[str, Any] = {}
    for name, meta in (columns or {}).items():
        if not isinstance(meta, dict):
            raise ValueError(f"GeoParquet column metadata for {name!r} must be a dict, got {type(meta).__name__}")
        declared[name] = dict(meta)
    for name, meta in (geo.get("columns") or {}).items():
        if isinstance(meta, dict):
            declared.setdefault(name, dict(meta))

    primary = declared.setdefault(primary_column, {})
    primary.setdefault("encoding", encoding)
    primary.setdefault("geometry_types", list(geometry_types) if geometry_types else [])
    if crs is not None:
        primary["crs"] = crs
    if bbox is not None:
        primary["bbox"] = list(bbox)
    geo["columns"] = declared
    return geo


def geo_column_metadata(geo_metadata: dict[str, Any], column: str | None = None) -> dict[str, Any]:
    """Return the per-column metadata entry for ``column`` (default: primary)."""
    if not geo_metadata:
        return {}
    name = column or geo_metadata.get("primary_column", DEFAULT_GEOMETRY_COLUMN)
    entry = (geo_metadata.get("columns") or {}).get(name)
    return entry if isinstance(entry, dict) else {}


def dumps_geo_metadata(geo_metadata: dict[str, Any]) -> bytes:
    """Serialize ``geo`` metadata to compact UTF-8 JSON bytes for Arrow schema metadata."""
    return json.dumps(geo_metadata, separators=(",", ":")).encode("utf-8")


def _shapely():
    """Import shapely lazily so raw-WKB workflows never require it."""
    try:
        import shapely.geometry
        import shapely.wkb
    except ImportError as exc:
        raise ImportError(
            "Decoding WKB geometry requires Shapely. Install with: pip install iterabledata[geospatial]"
        ) from exc
    return shapely


def wkb_to_geometry(wkb: bytes | bytearray | memoryview) -> dict[str, Any]:
    """Decode WKB bytes to a GeoJSON-like geometry mapping via Shapely."""
    shapely = _shapely()
    geom = shapely.wkb.loads(bytes(wkb))
    return dict(shapely.geometry.mapping(geom))


def feature_row_from_wkb(
    row: dict[str, Any],
    geometry_column: str = DEFAULT_GEOMETRY_COLUMN,
) -> dict[str, Any]:
    """Convert a raw row with WKB bytes into a feature-shaped row.

    The result mirrors the FlatGeobuf row shape: ``{"geometry": <GeoJSON-like
    mapping>, **<remaining fields as properties>}``. Rows whose geometry value
    is missing or already a mapping pass through with the geometry key moved
    first.
    """
    geometry = row.get(geometry_column)
    if isinstance(geometry, (bytes, bytearray, memoryview)):
        geometry = wkb_to_geometry(geometry)
    properties = {key: value for key, value in row.items() if key != geometry_column}
    return {"geometry": geometry, **properties}
