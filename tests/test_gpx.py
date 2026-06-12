"""Tests for GPX (GPS Exchange Format) format support."""

import os

from iterable.datatypes import GPXIterable
from iterable.helpers.detect import detect_file_type, open_iterable

# Minimal GPX 1.1 with one waypoint, one route point, one track point
SAMPLE_GPX = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="52.1" lon="4.2">
    <name>Waypoint A</name>
    <ele>10.5</ele>
  </wpt>
  <rte>
    <name>Route 1</name>
    <rtept lat="52.2" lon="4.3">
      <ele>11</ele>
    </rtept>
  </rte>
  <trk>
    <name>Track 1</name>
    <trkseg>
      <trkpt lat="52.3" lon="4.4">
        <time>2024-01-01T12:00:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""

GPX_FILE = "testdata/sample.gpx"


def _ensure_gpx():
    os.makedirs(os.path.dirname(GPX_FILE), exist_ok=True)
    if not os.path.exists(GPX_FILE):
        with open(GPX_FILE, "w", encoding="utf-8") as f:
            f.write(SAMPLE_GPX)


class TestGPX:
    def test_id(self):
        assert GPXIterable.id() == "gpx"

    def test_flatonly(self):
        assert GPXIterable.is_flatonly() is False

    def test_has_totals(self):
        assert GPXIterable.has_totals() is True

    def test_open_and_read(self):
        _ensure_gpx()
        with open_iterable(GPX_FILE) as it:
            rows = list(it)
        assert len(rows) == 3  # one wpt, one rtept, one trkpt
        for row in rows:
            assert "lat" in row
            assert "lon" in row
            assert "point_type" in row
            assert row["point_type"] in ("waypoint", "route", "track")

    def test_gpx_iterable_direct(self):
        _ensure_gpx()
        it = GPXIterable(GPX_FILE)
        assert it.totals() == 3
        row = it.read()
        assert row["lat"] == 52.1
        assert row["lon"] == 4.2
        assert row.get("name") == "Waypoint A"
        assert row.get("ele") == 10.5
        it.close()

    def test_automatic_detection(self):
        _ensure_gpx()
        r = detect_file_type(GPX_FILE)
        assert r["success"] is True
        assert r["datatype"] is GPXIterable

    def test_point_types_present(self):
        _ensure_gpx()
        with open_iterable(GPX_FILE) as it:
            rows = list(it)
        types = {r["point_type"] for r in rows}
        assert "waypoint" in types
        assert "route" in types
        assert "track" in types
