import pytest

pyarrow = pytest.importorskip("pyarrow")

from iterable.datatypes.geoparquet import GeoParquetIterable  # noqa: E402


def test_geoparquet_preserves_geo_metadata(tmp_path):
    path = tmp_path / "points.parquet"
    with GeoParquetIterable(str(path), mode="w", geometry_column="geometry", crs="EPSG:4326") as output:
        output.write_bulk([{"geometry": b"wkb", "name": "origin"}])

    metadata = pyarrow.parquet.ParquetFile(path).schema_arrow.metadata
    assert b"geo" in metadata
    with GeoParquetIterable(str(path)) as source:
        assert source.read()["geometry"] == b"wkb"
