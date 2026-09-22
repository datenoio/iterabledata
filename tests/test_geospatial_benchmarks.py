"""Benchmarks for geospatial format hot paths.

- GeoParquet: footer/metadata detection (open + geo metadata parse) on a
  wide-row file, proving detection stays metadata-only.
- FlatGeobuf: bounding-box selection through the packed spatial index vs an
  unindexed full scan over the same data.

Excluded from the default run via addopts; run with:
    pytest tests/test_geospatial_benchmarks.py -m benchmark --benchmark-only
"""

import pytest

pytest.importorskip("pytest_benchmark", reason="pytest-benchmark not installed (pip install pytest-benchmark)")
pytest.importorskip("pyarrow")
pytest.importorskip("fiona", reason="fiona not installed (pip install iterabledata[geospatial])")

import pyarrow.parquet  # noqa: E402  (also binds the ``pyarrow`` name)
from shapely.geometry import Point  # noqa: E402
from shapely.wkb import dumps as wkb_dumps  # noqa: E402

from iterable.datatypes.flatgeobuf import FlatGeobufIterable  # noqa: E402
from iterable.datatypes.geoparquet import GeoParquetIterable  # noqa: E402
from iterable.helpers.geo import build_geo_metadata, dumps_geo_metadata  # noqa: E402

pytestmark = pytest.mark.benchmark

NUM_ROWS = 20000
# Points on a 150x150-ish grid; the query bbox covers a ~10x10 corner cell.
GRID = 150
QUERY_BBOX = (0.0, 0.0, 10.0, 10.0)


def _point_rows(count):
    for i in range(count):
        x, y = float(i % GRID), float(i // GRID)
        yield {"id": i, "geometry": wkb_dumps(Point(x, y))}


@pytest.fixture(scope="module")
def geoparquet_source(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("bench") / "points.geoparquet")
    table = pyarrow.Table.from_pylist(list(_point_rows(NUM_ROWS)))
    geo = build_geo_metadata(
        primary_column="geometry",
        crs="EPSG:4326",
        geometry_types=["Point"],
        bbox=[0.0, 0.0, float(GRID), float(NUM_ROWS // GRID)],
    )
    table = table.replace_schema_metadata({b"geo": dumps_geo_metadata(geo)})
    pyarrow.parquet.write_table(table, path)
    return path


@pytest.fixture(scope="module")
def flatgeobuf_source(tmp_path_factory):
    base = tmp_path_factory.mktemp("benchfgb")
    indexed = str(base / "points.fgb")
    plain = str(base / "points_noindex.fgb")
    for path, kwargs in ((indexed, {}), (plain, {"spatial_index": False})):
        with FlatGeobufIterable(path, mode="w", crs="EPSG:4326", **kwargs) as dest:
            for i in range(NUM_ROWS):
                x, y = float(i % GRID), float(i // GRID)
                dest.write({"id": str(i), "geometry": {"type": "Point", "coordinates": (x, y)}})
    return indexed, plain


class TestGeoParquetMetadataDetection:
    def test_metadata_detection(self, benchmark, geoparquet_source):
        """Open + geo metadata parse; must read only the footer, not the rows."""

        def detect():
            with GeoParquetIterable(geoparquet_source) as source:
                return source.crs(), source.geometry_types(), source.bbox()

        crs, types, bbox = benchmark(detect)
        assert crs == "EPSG:4326" and types == ["Point"] and bbox is not None

    def test_metadata_detection_vs_plain_open(self, benchmark, geoparquet_source):
        """Baseline: pyarrow footer-only open for comparison."""

        def detect():
            reader = pyarrow.parquet.ParquetFile(geoparquet_source)
            return reader.schema_arrow.metadata

        metadata = benchmark(detect)
        assert b"geo" in metadata

    def test_first_batch_read(self, benchmark, geoparquet_source):
        def read_chunk():
            with GeoParquetIterable(geoparquet_source, batch_size=256) as source:
                return source.read_bulk(256)

        rows = benchmark(read_chunk)
        assert len(rows) == 256


class TestFlatGeobufBboxSelection:
    def _count_bbox(self, path):
        with FlatGeobufIterable(path, bbox=QUERY_BBOX) as source:
            return len(source.read_bulk(NUM_ROWS + 100))

    def test_bbox_with_spatial_index(self, benchmark, flatgeobuf_source):
        indexed, _ = flatgeobuf_source
        count = benchmark(self._count_bbox, indexed)
        assert 0 < count < NUM_ROWS

    def test_bbox_without_spatial_index(self, benchmark, flatgeobuf_source):
        """Same query on the unindexed copy: GDAL falls back to a full scan."""
        _, plain = flatgeobuf_source
        count = benchmark(self._count_bbox, plain)
        assert 0 < count < NUM_ROWS

    def test_full_scan(self, benchmark, flatgeobuf_source):
        """Baseline: unfiltered sequential scan of the indexed file."""
        indexed, _ = flatgeobuf_source

        def count_all():
            with FlatGeobufIterable(indexed) as source:
                return len(source.read_bulk(NUM_ROWS + 100))

        assert benchmark(count_all) == NUM_ROWS
