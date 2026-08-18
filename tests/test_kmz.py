"""Tests for KMZ (KML Zipped) format support."""

import os
import zipfile

import pytest
from optional_datatypes import require_datatype

from iterable.helpers.detect import open_iterable

KMZIterable = require_datatype("KMZIterable")

FIXTURE_KML = "fixtures/2cols6rows.kml"
KMZ_OUT = "testdata/sample.kmz"


def _ensure_kmz():
    """Create a KMZ file (ZIP with doc.kml) from the KML fixture if missing."""
    os.makedirs(os.path.dirname(KMZ_OUT), exist_ok=True)
    if os.path.exists(KMZ_OUT):
        return
    if not os.path.exists(FIXTURE_KML):
        pytest.skip(f"Fixture {FIXTURE_KML} not found")
    with zipfile.ZipFile(KMZ_OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(FIXTURE_KML, "doc.kml")


def _kmz_no_kml(tmp_path):
    """Create a KMZ (ZIP) that contains no .kml file."""
    p = tmp_path / "empty.kmz"
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("readme.txt", "no kml here")
    return str(p)


class TestKMZ:
    def test_id(self):
        assert KMZIterable.id() == "kmz"

    def test_flatonly(self):
        assert KMZIterable.is_flatonly() is False

    def test_has_totals(self):
        assert KMZIterable.has_totals() is True

    def test_open_and_read(self):
        _ensure_kmz()
        with open_iterable(KMZ_OUT) as it:
            rows = list(it)
        assert len(rows) >= 1
        for row in rows:
            assert isinstance(row, dict)
            assert row.get("type") == "Feature"
            assert "geometry" in row

    def test_kmz_iterable_direct(self):
        _ensure_kmz()
        it = KMZIterable(KMZ_OUT)
        assert it.totals() >= 1
        row = it.read()
        assert "geometry" in row
        it.close()

    def test_automatic_detection(self):
        _ensure_kmz()
        from iterable.helpers.detect import detect_file_type

        r = detect_file_type(KMZ_OUT)
        assert r["success"] is True
        assert r["datatype"] is KMZIterable

    def test_kmz_no_kml_raises(self, tmp_path):
        path = _kmz_no_kml(tmp_path)
        with pytest.raises(ValueError, match="No KML document found"):
            KMZIterable(path)
