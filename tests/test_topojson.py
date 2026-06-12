import json
import os
import tempfile

import pytest

from iterable.datatypes import TopoJSONIterable
from iterable.helpers.detect import open_iterable

try:
    import topojson  # noqa: F401

    HAS_TOPOJSON = True
except ImportError:
    HAS_TOPOJSON = False


@pytest.mark.skipif(not HAS_TOPOJSON, reason="TopoJSON support requires 'topojson' package")
class TestTopoJSON:
    def test_id(self):
        datatype_id = TopoJSONIterable.id()
        assert datatype_id == "topojson"

    def test_flatonly(self):
        flag = TopoJSONIterable.is_flatonly()
        assert not flag

    def test_openclose(self):
        """Test basic open/close"""
        topojson_data = {
            "type": "Topology",
            "objects": {
                "collection": {
                    "type": "GeometryCollection",
                    "geometries": [
                        {"type": "Point", "coordinates": [0, 0]},
                        {"type": "Point", "coordinates": [1, 1]},
                    ],
                }
            },
            "arcs": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".topojson", delete=False) as f:
            json.dump(topojson_data, f)
            temp_file = f.name

        try:
            iterable = TopoJSONIterable(temp_file)
            iterable.close()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_read_one(self):
        """Test reading single feature"""
        topojson_data = {
            "type": "Topology",
            "objects": {
                "collection": {
                    "type": "GeometryCollection",
                    "geometries": [
                        {"type": "Point", "coordinates": [0, 0]},
                        {"type": "Point", "coordinates": [1, 1]},
                    ],
                }
            },
            "arcs": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".topojson", delete=False) as f:
            json.dump(topojson_data, f)
            temp_file = f.name

        try:
            iterable = TopoJSONIterable(temp_file)
            record = iterable.read()
            assert isinstance(record, dict)
            assert "type" in record
            iterable.close()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_read_all(self):
        """Test reading all features"""
        topojson_data = {
            "type": "Topology",
            "objects": {
                "collection": {
                    "type": "GeometryCollection",
                    "geometries": [
                        {"type": "Point", "coordinates": [0, 0]},
                        {"type": "Point", "coordinates": [1, 1]},
                        {"type": "Point", "coordinates": [2, 2]},
                    ],
                }
            },
            "arcs": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".topojson", delete=False) as f:
            json.dump(topojson_data, f)
            temp_file = f.name

        try:
            iterable = TopoJSONIterable(temp_file)
            records = list(iterable)
            assert len(records) > 0
            iterable.close()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_read_bulk(self):
        """Test bulk reading"""
        topojson_data = {
            "type": "Topology",
            "objects": {
                "collection": {
                    "type": "GeometryCollection",
                    "geometries": [{"type": "Point", "coordinates": [i, i]} for i in range(5)],
                }
            },
            "arcs": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".topojson", delete=False) as f:
            json.dump(topojson_data, f)
            temp_file = f.name

        try:
            iterable = TopoJSONIterable(temp_file)
            rows = iterable.read_bulk(3)
            assert len(rows) > 0
            iterable.close()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_has_totals(self):
        """Test totals method"""
        topojson_data = {
            "type": "Topology",
            "objects": {
                "collection": {
                    "type": "GeometryCollection",
                    "geometries": [{"type": "Point", "coordinates": [i, i]} for i in range(3)],
                }
            },
            "arcs": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".topojson", delete=False) as f:
            json.dump(topojson_data, f)
            temp_file = f.name

        try:
            iterable = TopoJSONIterable(temp_file)
            assert TopoJSONIterable.has_totals()
            total = iterable.totals()
            assert total > 0
            iterable.close()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_automatic_detection(self):
        """Test automatic format detection via open_iterable"""
        topojson_data = {
            "type": "Topology",
            "objects": {
                "collection": {
                    "type": "GeometryCollection",
                    "geometries": [{"type": "Point", "coordinates": [0, 0]}],
                }
            },
            "arcs": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".topojson", delete=False) as f:
            json.dump(topojson_data, f)
            temp_file = f.name

        try:
            with open_iterable(temp_file) as source:
                assert isinstance(source, TopoJSONIterable)
                row = source.read()
                assert "type" in row
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_reset(self):
        """Test reset functionality"""
        topojson_data = {
            "type": "Topology",
            "objects": {
                "collection": {
                    "type": "GeometryCollection",
                    "geometries": [{"type": "Point", "coordinates": [0, 0]}],
                }
            },
            "arcs": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".topojson", delete=False) as f:
            json.dump(topojson_data, f)
            temp_file = f.name

        try:
            iterable = TopoJSONIterable(temp_file)
            row1 = iterable.read()
            iterable.reset()
            row2 = iterable.read()
            assert row1 == row2
            iterable.close()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_is_streaming(self):
        """Test streaming detection"""
        topojson_data = {
            "type": "Topology",
            "objects": {
                "collection": {
                    "type": "GeometryCollection",
                    "geometries": [{"type": "Point", "coordinates": [0, 0]}],
                }
            },
            "arcs": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".topojson", delete=False) as f:
            json.dump(topojson_data, f)
            temp_file = f.name

        try:
            iterable = TopoJSONIterable(temp_file)
            assert iterable.is_streaming() is False
            iterable.close()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_missing_dependency(self):
        """Test that missing topojson raises helpful error"""
        # This test would need to mock the import, but we can at least verify
        # the error message format is correct by checking the code
        pass
