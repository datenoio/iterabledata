"""FlatGeobuf detection, streaming read/write, bbox selection and edge cases."""

import tracemalloc

import pytest

fiona = pytest.importorskip("fiona", reason="fiona not installed (pip install iterabledata[geospatial])")

from iterable.datatypes.flatgeobuf import FlatGeobufIterable  # noqa: E402
from iterable.exceptions import FormatParseError, WriteError  # noqa: E402
from iterable.helpers.detect import detect_file_type  # noqa: E402

FIXTURE_POINTS = "fixtures/2cols6rows.fgb"
FIXTURE_SHAPES = "fixtures/geoshapes.fgb"
FIXTURE_NOINDEX = "fixtures/geoshapes_noindex.fgb"

POINT_FEATURE = {"geometry": {"type": "Point", "coordinates": (1.0, 2.0)}, "id": "1", "name": "origin"}


class TestDetection:
    """Task 3.1: extension and magic-byte detection."""

    def test_extension_detection(self):
        assert detect_file_type("features.fgb")["datatype"].id() == "flatgeobuf"

    def test_extension_detection_uppercase(self):
        assert detect_file_type("FEATURES.FGB")["datatype"].id() == "flatgeobuf"

    def test_magic_byte_detection(self):
        with open(FIXTURE_POINTS, "rb") as fileobj:
            result = detect_file_type("unknown.bin", fileobj=fileobj)
        assert result["datatype"].id() == "flatgeobuf"
        assert result["detection_method"] == "magic_number"

    def test_open_iterable_by_extension(self):
        from iterable import open_iterable

        with open_iterable(FIXTURE_POINTS) as source:
            assert isinstance(source, FlatGeobufIterable)
            assert source.totals() == 6


class TestMissingDependency:
    """Task 3.1: clear missing-dependency errors."""

    def test_missing_fiona_names_geospatial_extra(self, monkeypatch):
        monkeypatch.setattr("iterable.datatypes.flatgeobuf.fiona", None)
        with pytest.raises(ImportError, match=r"pip install iterabledata\[geospatial\]"):
            FlatGeobufIterable(FIXTURE_POINTS)

    def test_missing_fiona_write_mode(self, monkeypatch, tmp_path):
        monkeypatch.setattr("iterable.datatypes.flatgeobuf.fiona", None)
        with pytest.raises(ImportError, match=r"iterabledata\[geospatial\]"):
            FlatGeobufIterable(str(tmp_path / "x.fgb"), mode="w")

    def test_stream_input_rejected(self):
        with pytest.raises(ValueError, match="local filename"):
            FlatGeobufIterable(stream=object())


class TestStreamingReads:
    """Task 3.2/3.3 behavior exercised through golden fixtures."""

    def test_read_all_and_eof(self):
        with FlatGeobufIterable(FIXTURE_POINTS) as source:
            rows = source.read_bulk(100)
            assert len(rows) == 6
            assert source.read_bulk(10) == []
            with pytest.raises(StopIteration):
                source.read()

    def test_row_shape(self):
        with FlatGeobufIterable(FIXTURE_POINTS) as source:
            row = source.read()
            assert row["geometry"]["type"] == "Point"
            assert set(row) == {"geometry", "id", "name"}

    def test_mixed_geometry_types_fixture(self):
        with FlatGeobufIterable(FIXTURE_SHAPES) as source:
            kinds = sorted(row["kind"] for row in source.read_bulk(10))
            assert kinds == ["LineString", "Point", "Polygon"]

    def test_crs_metadata_available(self):
        with fiona.open(FIXTURE_SHAPES) as reference:
            assert reference.crs.to_epsg() == 3857

    def test_bbox_with_index_selects_subset(self):
        with FlatGeobufIterable(FIXTURE_POINTS, bbox=(1.5, 1.5, 3.5, 3.5)) as source:
            ids = sorted(row["id"] for row in source.read_bulk(100))
            assert ids == ["2", "3"]

    def test_bbox_missing_index_falls_back(self):
        """Without a packed index the driver scans and filters identically."""
        # Box covers only the Point at (1000, 2000).
        with FlatGeobufIterable(FIXTURE_NOINDEX, bbox=(900.0, 1500.0, 1100.0, 2500.0)) as source:
            rows = source.read_bulk(100)
            assert [row["kind"] for row in rows] == ["Point"]
        # Same query against the indexed file must agree.
        with FlatGeobufIterable(FIXTURE_SHAPES, bbox=(900.0, 1500.0, 1100.0, 2500.0)) as source:
            assert [row["kind"] for row in source.read_bulk(100)] == ["Point"]

    def test_reset_replays(self):
        with FlatGeobufIterable(FIXTURE_POINTS, bbox=(1.5, 1.5, 3.5, 3.5)) as source:
            first = source.read()
            source.reset()
            assert source.read() == first


class TestWrites:
    """Task 3.4: bounded writes and round trips."""

    def test_write_read_round_trip(self, tmp_path):
        path = str(tmp_path / "out.fgb")
        with FlatGeobufIterable(FIXTURE_POINTS) as source:
            rows = source.read_bulk(100)
        with FlatGeobufIterable(path, mode="w", crs="EPSG:4326") as dest:
            dest.write_bulk(rows)
        with FlatGeobufIterable(path) as reread:
            assert reread.read_bulk(100) == rows

    def test_write_single_feature_accepts_read_shape(self, tmp_path):
        path = str(tmp_path / "single.fgb")
        with FlatGeobufIterable(path, mode="w", crs="EPSG:4326") as dest:
            dest.write(POINT_FEATURE)
        with FlatGeobufIterable(path) as source:
            rows = source.read_bulk(10)
            assert len(rows) == 1
            assert rows[0]["name"] == "origin"
            assert rows[0]["geometry"]["type"] == "Point"

    def test_write_geojson_feature_shape(self, tmp_path):
        path = str(tmp_path / "feature.fgb")
        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": (5.0, 6.0)},
            "properties": {"id": "9", "name": "geojson"},
        }
        with FlatGeobufIterable(path, mode="w") as dest:
            dest.write(feature)
        with FlatGeobufIterable(path) as source:
            rows = source.read_bulk(10)
            assert rows[0]["name"] == "geojson"
            assert tuple(rows[0]["geometry"]["coordinates"]) == (5.0, 6.0)

    def test_crs_round_trip(self, tmp_path):
        path = str(tmp_path / "crs.fgb")
        with FlatGeobufIterable(path, mode="w", crs="EPSG:3857") as dest:
            dest.write(POINT_FEATURE)
        with fiona.open(path) as reference:
            assert reference.crs.to_epsg() == 3857

    def test_bounded_interleaved_writes(self, tmp_path):
        """Single write() calls interleaved with write_bulk() all persist."""
        path = str(tmp_path / "bounded.fgb")
        with FlatGeobufIterable(path, mode="w") as dest:
            dest.write(POINT_FEATURE)
            dest.write_bulk([dict(POINT_FEATURE, id=str(i)) for i in range(2, 6)])
            dest.write(dict(POINT_FEATURE, id="6"))
        with FlatGeobufIterable(path) as source:
            assert source.totals() == 6

    def test_written_file_has_spatial_index_by_default(self, tmp_path):
        path = str(tmp_path / "indexed.fgb")
        with FlatGeobufIterable(path, mode="w", crs="EPSG:4326") as dest:
            for i in range(1, 7):
                dest.write({"geometry": {"type": "Point", "coordinates": (float(i), float(i))}, "id": str(i)})
        with FlatGeobufIterable(path, bbox=(1.5, 1.5, 3.5, 3.5)) as source:
            assert sorted(row["id"] for row in source.read_bulk(100)) == ["2", "3"]

    def test_spatial_index_disabled(self, tmp_path):
        path = str(tmp_path / "noidx.fgb")
        with FlatGeobufIterable(path, mode="w", spatial_index=False) as dest:
            dest.write(POINT_FEATURE)
        with FlatGeobufIterable(path) as source:
            assert source.totals() == 1

    def test_geometry_type_mismatch_fails_clearly(self, tmp_path):
        path = str(tmp_path / "mixed.fgb")
        with pytest.raises(WriteError, match="Failed to write FlatGeobuf feature"):
            with FlatGeobufIterable(path, mode="w") as dest:
                dest.write(POINT_FEATURE)
                dest.write({"geometry": {"type": "LineString", "coordinates": [(0, 0), (1, 1)]}, "id": "2"})

    def test_explicit_unknown_geometry_type_allows_mixed(self, tmp_path):
        path = str(tmp_path / "mixedok.fgb")
        with FlatGeobufIterable(path, mode="w", geometry_type="Unknown") as dest:
            dest.write(POINT_FEATURE)
            dest.write({"geometry": {"type": "LineString", "coordinates": [(0, 0), (1, 1)]}, "id": "2"})
        with FlatGeobufIterable(path) as source:
            assert source.totals() == 2


class TestMalformedInputs:
    """Task 4.2: malformed, truncated and empty inputs."""

    def test_truncated_file(self, tmp_path):
        path = tmp_path / "truncated.fgb"
        data = open(FIXTURE_POINTS, "rb").read()
        # Keep just past the magic bytes: the header is unreadable.
        path.write_bytes(data[:64])
        with pytest.raises((FormatParseError, fiona.errors.FionaError, OSError, ValueError)):
            FlatGeobufIterable(str(path))

    def test_garbage_file(self, tmp_path):
        path = tmp_path / "garbage.fgb"
        path.write_bytes(b"\x00" * 128)
        with pytest.raises((FormatParseError, fiona.errors.FionaError, OSError, ValueError)):
            FlatGeobufIterable(str(path))

    def test_empty_feature_collection(self, tmp_path):
        path = str(tmp_path / "empty.fgb")
        schema = {"geometry": "Point", "properties": {"id": "str"}}
        with fiona.open(path, "w", driver="FlatGeobuf", schema=schema, crs="EPSG:4326"):
            pass
        with FlatGeobufIterable(path) as source:
            assert source.totals() == 0
            assert source.read_bulk(10) == []
            with pytest.raises(StopIteration):
                source.read()


def test_flatgeobuf_read_bounded_memory(tmp_path):
    """Streaming many features keeps peak Python memory bounded."""
    path = str(tmp_path / "many.fgb")
    with FlatGeobufIterable(path, mode="w") as dest:
        for i in range(4096):
            dest.write(
                {
                    "geometry": {"type": "Point", "coordinates": (float(i % 64), float(i // 64))},
                    "id": str(i),
                    "name": "x" * 32,
                }
            )

    tracemalloc.start()
    count = 0
    with FlatGeobufIterable(path) as source:
        while True:
            chunk = source.read_bulk(100)
            if not chunk:
                break
            count += len(chunk)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert count == 4096
    assert peak < 64 * 1024 * 1024


def test_flatgeobuf_write_bounded_memory(tmp_path):
    """Writes stream feature-by-feature; peak memory stays bounded."""
    path = str(tmp_path / "many_write.fgb")
    tracemalloc.start()
    with FlatGeobufIterable(path, mode="w") as dest:
        for i in range(4096):
            dest.write({"geometry": {"type": "Point", "coordinates": (0.0, 0.0)}, "id": str(i), "name": "y" * 64})
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert peak < 64 * 1024 * 1024
    with FlatGeobufIterable(path) as source:
        assert source.totals() == 4096
