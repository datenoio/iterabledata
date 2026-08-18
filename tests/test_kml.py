import os

from fixdata import FIXTURES
from optional_datatypes import require_datatype

KMLIterable = require_datatype("KMLIterable")

# Create fixture file if it doesn't exist
FIXTURE_FILE = "fixtures/2cols6rows.kml"


def setup_module():
    """Create fixture file if it doesn't exist"""
    if not os.path.exists(FIXTURE_FILE):
        # Create a simple KML file with Placemarks
        kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
"""
        for i, record in enumerate(FIXTURES):
            kml_content += f"""  <Placemark>
    <name>{record["name"]}</name>
    <description>ID: {record["id"]}</description>
    <Point>
      <coordinates>{i},{i}</coordinates>
    </Point>
  </Placemark>
"""
        kml_content += """</Document>
</kml>"""

        os.makedirs(os.path.dirname(FIXTURE_FILE), exist_ok=True)
        with open(FIXTURE_FILE, "w", encoding="utf-8") as f:
            f.write(kml_content)


class TestKML:
    def test_id(self):
        datatype_id = KMLIterable.id()
        assert datatype_id == "kml"

    def test_flatonly(self):
        flag = KMLIterable.is_flatonly()
        assert not flag

    def test_openclose(self):
        iterable = KMLIterable(FIXTURE_FILE)
        iterable.close()

    def test_has_totals(self):
        iterable = KMLIterable(FIXTURE_FILE)
        assert KMLIterable.has_totals()
        total = iterable.totals()
        assert total == len(FIXTURES)
        iterable.close()

    def test_read(self):
        iterable = KMLIterable(FIXTURE_FILE)
        row = iterable.read()
        assert isinstance(row, dict)
        assert "type" in row
        assert row["type"] == "Feature"
        assert "geometry" in row
        iterable.close()

    def test_read_all(self):
        iterable = KMLIterable(FIXTURE_FILE)
        n = 0
        for row in iterable:
            assert isinstance(row, dict)
            assert "geometry" in row
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_write_read(self):
        iterable = KMLIterable("testdata/2cols6rows_test.kml", mode="w")
        # Create features
        for i, record in enumerate(FIXTURES):
            feature = {"type": "Feature", "properties": record, "geometry": {"type": "Point", "coordinates": [i, i]}}
            iterable.write(feature)
        iterable.close()

        iterable = KMLIterable("testdata/2cols6rows_test.kml")
        n = 0
        for row in iterable:
            assert isinstance(row, dict)
            assert "geometry" in row
            n += 1
        assert n == len(FIXTURES)
        iterable.close()
