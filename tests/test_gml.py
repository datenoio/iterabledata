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


WFS2_GML = """<?xml version="1.0" encoding="UTF-8"?>
<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0"
    xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:app="http://example.org/app">
  <wfs:member>
    <app:apotheke gml:id="a1"><app:name>Apotheke am Markt</app:name><app:plz>18055</app:plz>
      <app:geom><gml:Point srsName="EPSG:4326"><gml:pos>54.09 12.14</gml:pos></gml:Point></app:geom>
      <app:member>nested element that is not a feature member</app:member></app:apotheke>
  </wfs:member>
  <wfs:member>
    <app:apotheke gml:id="a2"><app:name>Linden-Apotheke</app:name><app:plz>18057</app:plz></app:apotheke>
  </wfs:member>
</wfs:FeatureCollection>
"""

SERVICE_NS_GML = """<?xml version="1.0" encoding="UTF-8"?>
<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs"
    xmlns:gml="http://www.opengis.net/gml" xmlns:hro="https://geo.sv.rostock.de">
  <hro:featureMember><hro:apotheken gml:id="1"><hro:name>Apotheke am Markt</hro:name>
    <hro:geometry><gml:Point srsName="EPSG:25833"><gml:pos>312000 6000000</gml:pos></gml:Point></hro:geometry>
  </hro:apotheken></hro:featureMember>
  <hro:featureMember><hro:apotheken gml:id="2"><hro:name>Linden</hro:name></hro:apotheken></hro:featureMember>
</wfs:FeatureCollection>
"""

FEATURE_MEMBERS_GML = """<?xml version="1.0"?>
<gml:FeatureCollection xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:app="urn:app">
  <gml:featureMembers>
    <app:School gml:id="s1"><app:name>A</app:name></app:School>
    <app:School gml:id="s2"><app:name>B</app:name></app:School>
  </gml:featureMembers>
</gml:FeatureCollection>
"""


def _read_gml(tmp_path, text, **iterableargs):
    from iterable.helpers.detect import open_iterable

    path = tmp_path / "features.gml"
    path.write_text(text, encoding="utf-8")
    with open_iterable(str(path), iterableargs=iterableargs) as source:
        return list(source)


def test_gml_wfs2_members(tmp_path):
    rows = _read_gml(tmp_path, WFS2_GML)
    assert [row["properties"]["name"] for row in rows] == ["Apotheke am Markt", "Linden-Apotheke"]
    assert rows[0]["geometry"] == {"type": "Point", "coordinates": [54.09, 12.14]}
    assert _read_gml(tmp_path, WFS2_GML, tagname="wfs:member") == rows
    assert _read_gml(tmp_path, WFS2_GML, feature_member="member") == rows


def test_gml_feature_member_in_a_service_namespace(tmp_path):
    rows = _read_gml(tmp_path, SERVICE_NS_GML)
    assert [row["properties"]["name"] for row in rows] == ["Apotheke am Markt", "Linden"]
    assert rows[0]["geometry"] == {"type": "Point", "coordinates": [312000.0, 6000000.0]}


def test_gml_tagname_naming_the_feature_element(tmp_path):
    rows = _read_gml(tmp_path, SERVICE_NS_GML, tagname="hro:apotheken")
    assert [row["properties"]["name"] for row in rows] == ["Apotheke am Markt", "Linden"]
    rows = _read_gml(tmp_path, WFS2_GML, tagname="app:apotheke")
    assert [row["properties"]["name"] for row in rows] == ["Apotheke am Markt", "Linden-Apotheke"]


def test_gml_feature_members_container(tmp_path):
    rows = _read_gml(tmp_path, FEATURE_MEMBERS_GML)
    assert [row["properties"]["name"] for row in rows] == ["A", "B"]


def test_gml_parse_errors_are_not_swallowed(tmp_path):
    import pytest

    from iterable.helpers.detect import open_iterable

    path = tmp_path / "empty.gml"
    path.write_text("", encoding="utf-8")
    with pytest.raises(Exception, match="(?i)empty|document"):
        list(open_iterable(str(path)))
