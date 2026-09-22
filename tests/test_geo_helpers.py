"""Geometry/CRS helper tests independent of file backends.

Covers iterable.helpers.geo: GeoParquet ``geo`` metadata parse/build round
trips, CRS/encoding/geometry-type/bbox extraction, and WKB -> GeoJSON-like
geometry decoding. No Parquet or FlatGeobuf files are involved.
"""

import struct
import sys

import pytest

from iterable.helpers.geo import (
    build_geo_metadata,
    dumps_geo_metadata,
    feature_row_from_wkb,
    geo_column_metadata,
    parse_geo_metadata,
    wkb_to_geometry,
)

VALID_GEO = {
    "version": "1.0.0",
    "primary_column": "geometry",
    "columns": {
        "geometry": {
            "encoding": "WKB",
            "geometry_types": ["Point", "Polygon"],
            "crs": "EPSG:4326",
            "bbox": [-10.0, -10.0, 10.0, 10.0],
        }
    },
}


class TestParseGeoMetadata:
    def test_none_and_empty(self):
        assert parse_geo_metadata(None) == {}
        assert parse_geo_metadata(b"") == {}
        assert parse_geo_metadata("") == {}

    def test_invalid_json_bytes(self):
        assert parse_geo_metadata(b"{not json") == {}

    def test_invalid_utf8(self):
        assert parse_geo_metadata(b"\xff\xfe{}") == {}

    def test_non_object_json(self):
        assert parse_geo_metadata(b'["Point"]') == {}
        assert parse_geo_metadata(b'"geometry"') == {}

    def test_wrong_type(self):
        assert parse_geo_metadata(123) == {}

    def test_valid_bytes_and_str(self):
        raw = dumps_geo_metadata(VALID_GEO)
        assert parse_geo_metadata(raw) == VALID_GEO
        assert parse_geo_metadata(raw.decode("utf-8")) == VALID_GEO


class TestBuildGeoMetadata:
    def test_defaults(self):
        geo = build_geo_metadata()
        assert geo["version"] == "1.0.0"
        assert geo["primary_column"] == "geometry"
        assert geo["columns"]["geometry"]["encoding"] == "WKB"
        assert geo["columns"]["geometry"]["geometry_types"] == []
        assert "crs" not in geo["columns"]["geometry"]

    def test_crs_types_and_bbox(self):
        geo = build_geo_metadata(
            primary_column="geom",
            crs="EPSG:3857",
            geometry_types=["Point"],
            bbox=(0.0, 0.0, 1.0, 1.0),
        )
        entry = geo["columns"]["geom"]
        assert entry["crs"] == "EPSG:3857"
        assert entry["geometry_types"] == ["Point"]
        assert entry["bbox"] == [0.0, 0.0, 1.0, 1.0]

    def test_existing_unknown_fields_preserved(self):
        existing = {"version": "1.1.0", "primary_column": "old", "custom": {"x": 1}}
        geo = build_geo_metadata(primary_column="geometry", existing=existing)
        assert geo["version"] == "1.1.0"  # existing version wins over default
        assert geo["custom"] == {"x": 1}
        assert geo["primary_column"] == "geometry"

    def test_additional_geometry_columns(self):
        geo = build_geo_metadata(
            primary_column="geom",
            columns={"centroid": {"encoding": "WKB", "geometry_types": ["Point"], "crs": "EPSG:4326"}},
        )
        assert set(geo["columns"]) == {"geom", "centroid"}
        assert geo["columns"]["centroid"]["crs"] == "EPSG:4326"

    def test_invalid_column_metadata_rejected(self):
        with pytest.raises(ValueError, match="must be a dict"):
            build_geo_metadata(columns={"centroid": "WKB"})

    def test_build_parse_round_trip(self):
        geo = build_geo_metadata(primary_column="geom", crs="EPSG:4326", bbox=[0, 0, 1, 1])
        assert parse_geo_metadata(dumps_geo_metadata(geo)) == geo


class TestGeoColumnMetadata:
    def test_primary_default(self):
        assert geo_column_metadata(VALID_GEO)["crs"] == "EPSG:4326"

    def test_named_column(self):
        geo = build_geo_metadata(columns={"centroid": {"encoding": "point"}})
        assert geo_column_metadata(geo, "centroid")["encoding"] == "point"

    def test_missing_column_and_empty_metadata(self):
        assert geo_column_metadata(VALID_GEO, "nope") == {}
        assert geo_column_metadata({}) == {}


# WKB for POINT (1 2): little-endian byte order, type 1, doubles 1.0/2.0
POINT_WKB = struct.pack("<BI2d", 1, 1, 1.0, 2.0)


class TestWkbToGeometry:
    shapely = pytest.importorskip("shapely")

    def test_point(self):
        geom = wkb_to_geometry(POINT_WKB)
        assert geom["type"] == "Point"
        assert tuple(geom["coordinates"]) == (1.0, 2.0)

    def test_accepts_bytearray_and_memoryview(self):
        assert wkb_to_geometry(bytearray(POINT_WKB))["type"] == "Point"
        assert wkb_to_geometry(memoryview(POINT_WKB))["type"] == "Point"

    def test_polygon(self):
        from shapely.geometry import Polygon
        from shapely.wkb import dumps

        geom = wkb_to_geometry(dumps(Polygon([(0, 0), (0, 1), (1, 1), (0, 0)])))
        assert geom["type"] == "Polygon"
        assert len(geom["coordinates"][0]) == 4

    def test_feature_row_decodes_geometry(self):
        row = {"geometry": POINT_WKB, "id": "7", "name": "Ada"}
        feature = feature_row_from_wkb(row)
        assert feature["geometry"]["type"] == "Point"
        assert feature["id"] == "7" and feature["name"] == "Ada"
        assert set(feature) == {"geometry", "id", "name"}

    def test_feature_row_custom_column_and_passthrough(self):
        row = {"geom": {"type": "Point", "coordinates": (0, 0)}, "id": 1}
        feature = feature_row_from_wkb(row, geometry_column="geom")
        assert feature["geometry"]["type"] == "Point"  # mapping passes through
        assert "geom" not in feature

    def test_missing_shapely_raises_importerror(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "shapely", None)
        monkeypatch.setitem(sys.modules, "shapely.wkb", None)
        monkeypatch.setitem(sys.modules, "shapely.geometry", None)
        with pytest.raises(ImportError, match="iterabledata\\[geospatial\\]"):
            wkb_to_geometry(POINT_WKB)
