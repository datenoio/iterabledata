import os

from fixdata import FIXTURES
from optional_datatypes import require_datatype

GMLIterable = require_datatype("GMLIterable")

# Create fixture file if it doesn't exist
FIXTURE_FILE = "fixtures/2cols6rows.gml"


def setup_module():
    """Create fixture file if it doesn't exist"""
    if not os.path.exists(FIXTURE_FILE):
        # Create a simple GML file with features
        gml_content = """<?xml version="1.0" encoding="UTF-8"?>
<gml:FeatureCollection xmlns:gml="http://www.opengis.net/gml/3.2">
"""
        for i, record in enumerate(FIXTURES):
            gml_content += f"""  <gml:featureMember>
    <gml:Feature>
      <name>{record["name"]}</name>
      <id>{record["id"]}</id>
      <gml:geometryProperty>
        <gml:Point>
          <gml:pos>{i} {i}</gml:pos>
        </gml:Point>
      </gml:geometryProperty>
    </gml:Feature>
  </gml:featureMember>
"""
        gml_content += """</gml:FeatureCollection>"""

        os.makedirs(os.path.dirname(FIXTURE_FILE), exist_ok=True)
        with open(FIXTURE_FILE, "w", encoding="utf-8") as f:
            f.write(gml_content)


class TestGML:
    def test_id(self):
        datatype_id = GMLIterable.id()
        assert datatype_id == "gml"

    def test_flatonly(self):
        flag = GMLIterable.is_flatonly()
        assert not flag

    def test_openclose(self):
        iterable = GMLIterable(FIXTURE_FILE)
        iterable.close()

    def test_has_totals(self):
        iterable = GMLIterable(FIXTURE_FILE)
        assert GMLIterable.has_totals()
        total = iterable.totals()
        assert total == len(FIXTURES)
        iterable.close()

    def test_read(self):
        iterable = GMLIterable(FIXTURE_FILE)
        row = iterable.read()
        assert isinstance(row, dict)
        assert "type" in row
        assert row["type"] == "Feature"
        iterable.close()

    def test_read_all(self):
        iterable = GMLIterable(FIXTURE_FILE)
        n = 0
        for row in iterable:
            assert isinstance(row, dict)
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_write_read(self):
        iterable = GMLIterable("testdata/2cols6rows_test.gml", mode="w")
        # Create features
        for i, record in enumerate(FIXTURES):
            feature = {"type": "Feature", "properties": record, "geometry": {"type": "Point", "coordinates": [i, i]}}
            iterable.write(feature)
        iterable.close()

        iterable = GMLIterable("testdata/2cols6rows_test.gml")
        n = 0
        for row in iterable:
            assert isinstance(row, dict)
            n += 1
        assert n == len(FIXTURES)
        iterable.close()
