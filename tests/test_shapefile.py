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


def _zipped_towns(tmp_path, cpg="1252", folder=""):
    import zipfile

    shapefile = pytest.importorskip("shapefile")
    base = str(tmp_path / "towns")
    writer = shapefile.Writer(base, shapeType=shapefile.POINT, encoding="cp1252")
    writer.field("name", "C", 40)
    writer.field("plz", "C", 5)
    writer.point(7.6, 47.8)
    writer.record("Müllheim", "79379")
    writer.point(8.5, 47.3)
    writer.record("Zürich", "8001")
    writer.close()
    with open(base + ".cpg", "w") as handle:
        handle.write(cpg)
    archive = str(tmp_path / ("towns.shp.zip" if not folder else "towns.zip"))
    with zipfile.ZipFile(archive, "w") as zipped:
        for ext in ("shp", "shx", "dbf", "cpg"):
            zipped.write(f"{base}.{ext}", f"{folder}towns.{ext}")
    return archive


def test_zipped_shapefile_through_open_iterable(tmp_path):
    from iterable.helpers.detect import open_iterable

    for archive in (_zipped_towns(tmp_path), _zipped_towns(tmp_path, folder="data/")):
        with open_iterable(archive) as source:
            assert isinstance(source, ShapefileIterable)
            rows = list(source)
        assert [row["properties"]["name"] for row in rows] == ["Müllheim", "Zürich"]
        assert rows[0]["geometry"] == {"type": "Point", "coordinates": [7.6, 47.8]}


def test_zipped_shapefile_direct_and_cpg_names(tmp_path):
    import contextlib

    from iterable.datatypes.shapefile import _PYSHP_READS_CPG, cpg_encoding

    archive = _zipped_towns(tmp_path, cpg="ANSI 1252")
    source = ShapefileIterable(archive)
    # pyshp >= 3 cannot use "ANSI 1252" itself and warns that the code page passed differs.
    expect = pytest.warns(UserWarning, match="cpg") if _PYSHP_READS_CPG else contextlib.nullcontext()
    with expect:
        assert source.read()["properties"]["name"] == "Müllheim"
    assert source.encoding == "cp1252"
    assert source.totals() == 2
    source.close()
    assert cpg_encoding("UTF-8") == "utf-8"
    assert cpg_encoding("65001") == "utf-8"
    assert cpg_encoding("1251") == "cp1251"
    assert cpg_encoding("ISO 8859-1") == "iso8859-1"
    assert cpg_encoding("shift_jis") == "shift_jis"
    assert cpg_encoding("") is None
    assert cpg_encoding("no-such-code-page") is None


def test_zip_with_several_shapefiles_needs_a_member(tmp_path):
    import zipfile

    from iterable.exceptions import ReadError

    single = _zipped_towns(tmp_path)
    archive = str(tmp_path / "two.zip")
    with zipfile.ZipFile(single) as source_zip, zipfile.ZipFile(archive, "w") as target:
        for name in source_zip.namelist():
            target.writestr("a/" + name, source_zip.read(name))
            target.writestr("b/" + name.replace("towns", "other"), source_zip.read(name))
    with pytest.raises(ReadError, match="exactly one .shp"):
        ShapefileIterable(archive)
    source = ShapefileIterable(archive, options={"member": "b/other.shp"})
    assert source.read()["properties"]["plz"] == "79379"
    source.close()
