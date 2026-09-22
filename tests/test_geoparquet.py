import struct
import tracemalloc

import pytest

pyarrow = pytest.importorskip("pyarrow")

from iterable.convert.batch import BatchSelection  # noqa: E402
from iterable.datatypes.geoparquet import GeoParquetIterable  # noqa: E402
from iterable.exceptions import FormatParseError  # noqa: E402
from iterable.helpers.geo import build_geo_metadata, dumps_geo_metadata  # noqa: E402

FIXTURE_POINTS = "fixtures/2cols6rows.geoparquet"
FIXTURE_SHAPES = "fixtures/geoshapes.parquet"
POINT_WKB = struct.pack("<BI2d", 1, 1, 1.0, 2.0)  # little-endian POINT (1 2)


def test_geoparquet_preserves_geo_metadata(tmp_path):
    path = tmp_path / "points.parquet"
    with GeoParquetIterable(str(path), mode="w", geometry_column="geometry", crs="EPSG:4326") as output:
        output.write_bulk([{"geometry": b"wkb", "name": "origin"}])

    metadata = pyarrow.parquet.ParquetFile(path).schema_arrow.metadata
    assert b"geo" in metadata
    with GeoParquetIterable(str(path)) as source:
        assert source.read()["geometry"] == b"wkb"


class TestGeoParquetMetadataExposure:
    """Task 2.2: geometry column, CRS, encoding, type and bbox metadata."""

    def test_metadata_accessors_from_fixture(self):
        with GeoParquetIterable(FIXTURE_POINTS) as source:
            assert source.primary_geometry_column == "geometry"
            assert source.crs() == "EPSG:4326"
            assert source.geometry_encoding() == "WKB"
            assert source.geometry_types() == ["Point"]
            assert source.bbox() == [1.0, 1.0, 6.0, 6.0]
            assert source.geo_metadata["version"] == "1.0.0"

    def test_multiple_geometry_types_fixture(self):
        with GeoParquetIterable(FIXTURE_SHAPES) as source:
            assert source.crs() == "EPSG:3857"
            assert source.geometry_types() == ["Point", "LineString", "Polygon"]
            assert source.bbox() == [0.0, 0.0, 1000.0, 2000.0]
            kinds = [row["kind"] for row in source.read_bulk(10)]
            assert kinds == ["Point", "LineString", "Polygon"]


class TestRowModes:
    def test_wkb_mode_returns_raw_bytes(self):
        with GeoParquetIterable(FIXTURE_POINTS, geometry_mode="wkb") as source:
            row = source.read()
            assert isinstance(row["geometry"], (bytes, bytearray))
            assert "id" in row and "name" in row

    def test_feature_mode_decodes_geometry(self):
        pytest.importorskip("shapely")
        with GeoParquetIterable(FIXTURE_POINTS, geometry_mode="feature") as source:
            row = source.read()
            assert row["geometry"]["type"] == "Point"
            coords = tuple(row["geometry"]["coordinates"])
            assert coords == (float(row["id"]),) * 2
            assert row["name"]

    def test_feature_mode_read_bulk(self):
        pytest.importorskip("shapely")
        with GeoParquetIterable(FIXTURE_SHAPES, geometry_mode="feature") as source:
            rows = source.read_bulk(10)
            assert [r["geometry"]["type"] for r in rows] == ["Point", "LineString", "Polygon"]
            assert all("geometry" in r and "kind" in r for r in rows)

    def test_invalid_geometry_mode_rejected(self):
        with pytest.raises(ValueError, match="geometry_mode"):
            GeoParquetIterable(FIXTURE_POINTS, geometry_mode="geojson")

    def test_wkb_mode_keeps_batch_and_projection(self):
        """Raw WKB mode reuses the Parquet batch/projection paths unchanged."""
        with GeoParquetIterable(FIXTURE_POINTS) as source:
            batches = list(source.read_batches(BatchSelection(columns=("id",), batch_size=2)))
            assert batches
            assert all(set(row.keys()) == {"id"} for batch in batches for row in batch)


class TestProfileValidation:
    def test_plain_parquet_rejected_by_default(self):
        with pytest.raises(FormatParseError, match="no valid GeoParquet"):
            GeoParquetIterable("fixtures/2cols6rows.parquet")

    def test_invalid_geo_json_rejected(self, tmp_path):
        path = tmp_path / "badgeo.parquet"
        table = pyarrow.Table.from_pylist([{"geometry": POINT_WKB, "id": 1}])
        table = table.replace_schema_metadata({b"geo": b"{not valid json"})
        pyarrow.parquet.write_table(table, path)
        with pytest.raises(FormatParseError):
            GeoParquetIterable(str(path))

    def test_validation_opt_out(self):
        with GeoParquetIterable("fixtures/2cols6rows.parquet", validate_metadata=False) as source:
            assert source.geo_metadata == {}
            assert source.read()["id"] == 1

    def test_explicit_profile_on_fixture(self):
        from iterable import open_iterable

        with open_iterable(FIXTURE_POINTS, iterableargs={"format": "geoparquet"}) as source:
            assert source.geometry_types() == ["Point"]


class TestGeoParquetWrites:
    def test_round_trip_feature_rows(self, tmp_path):
        pytest.importorskip("shapely")
        path = tmp_path / "rt.geoparquet"
        rows = [{"geometry": POINT_WKB, "id": 1, "name": "origin"}]
        with GeoParquetIterable(
            str(path), mode="w", crs="EPSG:4326", geometry_types=["Point"], bbox=[1.0, 2.0, 1.0, 2.0]
        ) as output:
            output.write_bulk(rows)
        with GeoParquetIterable(str(path), geometry_mode="feature") as source:
            assert source.crs() == "EPSG:4326"
            assert source.geometry_types() == ["Point"]
            assert source.bbox() == [1.0, 2.0, 1.0, 2.0]
            row = source.read()
            assert row["geometry"] == {"type": "Point", "coordinates": (1.0, 2.0)}
            assert row["name"] == "origin"

    def test_multiple_geometry_columns(self, tmp_path):
        path = tmp_path / "multi.geoparquet"
        with GeoParquetIterable(
            str(path),
            mode="w",
            geometry_column="geometry",
            crs="EPSG:4326",
            geometry_columns={"centroid": {"encoding": "WKB", "geometry_types": ["Point"], "crs": "EPSG:4326"}},
        ) as output:
            output.write_bulk([{"geometry": POINT_WKB, "centroid": POINT_WKB, "id": 1}])
        with GeoParquetIterable(str(path)) as source:
            assert source.primary_geometry_column == "geometry"
            assert source.crs("centroid") == "EPSG:4326"
            assert source.geometry_types("centroid") == ["Point"]

    def test_inconsistent_metadata_fails_clearly(self, tmp_path):
        path = tmp_path / "bad.geoparquet"

        class NotSerializable:
            pass

        # The metadata error surfaces when buffered records are flushed (at close()).
        with pytest.raises(ValueError, match="Invalid GeoParquet metadata"):
            with GeoParquetIterable(str(path), mode="w", crs=NotSerializable()) as output:
                output.write({"geometry": POINT_WKB})

    def test_invalid_column_metadata_fails(self, tmp_path):
        with pytest.raises(ValueError, match="Invalid GeoParquet metadata"):
            with GeoParquetIterable(str(tmp_path / "x.geoparquet"), mode="w", geometry_columns={"c": "WKB"}) as output:
                output.write({"geometry": POINT_WKB})


class TestMalformedInputs:
    def test_zero_rows_with_valid_metadata(self, tmp_path):
        """A valid GeoParquet schema with zero rows reads as empty."""
        path = tmp_path / "zerorows.geoparquet"
        table = pyarrow.Table.from_pylist(
            [],
            schema=pyarrow.schema([("geometry", pyarrow.binary()), ("id", pyarrow.int64())]),
        )
        geo = build_geo_metadata(primary_column="geometry", crs="EPSG:4326", geometry_types=["Point"])
        table = table.replace_schema_metadata({b"geo": dumps_geo_metadata(geo)})
        pyarrow.parquet.write_table(table, path)
        with GeoParquetIterable(str(path)) as source:
            assert source.totals() == 0
            assert source.crs() == "EPSG:4326"
            assert source.read_bulk(10) == []
            with pytest.raises(StopIteration):
                source.read()

    def test_truncated_file(self, tmp_path):
        path = tmp_path / "truncated.geoparquet"
        data = open(FIXTURE_POINTS, "rb").read()
        path.write_bytes(data[: len(data) // 2])
        with pytest.raises(FormatParseError):
            GeoParquetIterable(str(path))

    def test_empty_file(self, tmp_path):
        path = tmp_path / "empty.geoparquet"
        path.write_bytes(b"")
        with pytest.raises(FormatParseError):
            GeoParquetIterable(str(path))

    def test_garbage_file(self, tmp_path):
        path = tmp_path / "garbage.geoparquet"
        path.write_bytes(b"\x00" * 64)
        with pytest.raises(FormatParseError):
            GeoParquetIterable(str(path))


def test_geoparquet_read_bounded_memory(tmp_path):
    """Streaming reads stay bounded regardless of file row count."""
    path = tmp_path / "many.geoparquet"
    rows = [{"geometry": POINT_WKB, "id": i, "name": "x" * 32} for i in range(4096)]
    with GeoParquetIterable(str(path), mode="w", batch_size=256) as output:
        output.write_bulk(rows)

    tracemalloc.start()
    count = 0
    with GeoParquetIterable(str(path), batch_size=64) as source:
        while True:
            chunk = source.read_bulk(50)
            if not chunk:
                break
            count += len(chunk)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert count == len(rows)
    assert peak < 32 * 1024 * 1024
