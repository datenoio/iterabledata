import os

import pytest
from fixdata import FIXTURES

from iterable.datatypes import ShapefileIterable

# Create fixture file if it doesn't exist
FIXTURE_FILE = "fixtures/2cols6rows.shp"


def setup_module():
    """Create fixture file if it doesn't exist"""
    try:
        import shapefile
    except ImportError:
        pytest.skip("pyshp library not available")

    if not os.path.exists(FIXTURE_FILE):
        # Create a simple shapefile
        w = shapefile.Writer(FIXTURE_FILE.replace(".shp", ""))
        w.field("id", "C", 10)
        w.field("name", "C", 50)

        for i, record in enumerate(FIXTURES):
            w.point(i, i)
            w.record(record["id"], record["name"])

        w.close()


class TestShapefile:
    def test_id(self):
        datatype_id = ShapefileIterable.id()
        assert datatype_id == "shapefile"

    def test_flatonly(self):
        flag = ShapefileIterable.is_flatonly()
        assert not flag

    def test_openclose(self):
        try:
            iterable = ShapefileIterable(FIXTURE_FILE)
            iterable.close()
        except ImportError:
            pytest.skip("pyshp library not available")

    def test_has_totals(self):
        try:
            iterable = ShapefileIterable(FIXTURE_FILE)
            assert ShapefileIterable.has_totals()
            total = iterable.totals()
            assert total == len(FIXTURES)
            iterable.close()
        except ImportError:
            pytest.skip("pyshp library not available")

    def test_read(self):
        try:
            iterable = ShapefileIterable(FIXTURE_FILE)
            row = iterable.read()
            assert isinstance(row, dict)
            assert "type" in row
            assert row["type"] == "Feature"
            assert "geometry" in row
            iterable.close()
        except ImportError:
            pytest.skip("pyshp library not available")

    def test_read_all(self):
        try:
            iterable = ShapefileIterable(FIXTURE_FILE)
            n = 0
            for row in iterable:
                assert isinstance(row, dict)
                assert "geometry" in row
                n += 1
            assert n == len(FIXTURES)
            iterable.close()
        except ImportError:
            pytest.skip("pyshp library not available")

    def test_reset(self):
        iterable = ShapefileIterable(FIXTURE_FILE)
        first = iterable.read()
        iterable.reset()
        assert iterable.read() == first
        iterable.close()

    def test_write_read(self):
        try:
            iterable = ShapefileIterable("testdata/2cols6rows_test.shp", mode="w")
            # Create features
            for i, record in enumerate(FIXTURES):
                feature = {
                    "type": "Feature",
                    "properties": record,
                    "geometry": {"type": "Point", "coordinates": [i, i]},
                }
                iterable.write(feature)
            iterable.close()

            iterable = ShapefileIterable("testdata/2cols6rows_test.shp")
            n = 0
            for row in iterable:
                assert isinstance(row, dict)
                assert "geometry" in row
                n += 1
            assert n == len(FIXTURES)
            iterable.close()
        except ImportError:
            pytest.skip("pyshp library not available")


class TestShapefileStreaming:
    """Shapefile features must be read lazily in bounded memory."""

    ROWS = 100_000

    def _write_large(self, base_path):
        import shapefile

        w = shapefile.Writer(base_path)
        w.field("id", "N", 10)
        w.field("name", "C", 120)
        for i in range(self.ROWS):
            w.point(i % 360 - 180, i % 180 - 90)
            w.record(i, f"name-{i}-{'x' * 100}")
        w.close()

    def test_is_streaming(self):
        iterable = ShapefileIterable(FIXTURE_FILE)
        assert iterable.is_streaming()
        iterable.close()

    def test_large_read_bounded_memory(self, tmp_path):
        import tracemalloc

        base = str(tmp_path / "large")
        self._write_large(base)
        uncompressed_size = self.ROWS * 130

        iterable = ShapefileIterable(base + ".shp")
        tracemalloc.start()
        n = 0
        for feature in iterable:
            assert feature["properties"]["id"] == n
            n += 1
        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        iterable.close()

        assert n == self.ROWS
        # Lazy iteration keeps peak allocation far below the full payload.
        assert peak < uncompressed_size / 2, f"peak {peak} suggests full-file load"
