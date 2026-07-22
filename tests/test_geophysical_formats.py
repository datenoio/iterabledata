"""Tests for geophysical formats (SEG-Y, GRIB2, miniSEED).

Skip when optional backends are missing.
"""

from __future__ import annotations

import pytest

from iterable.datatypes.grib2 import HAS_GRIB, GRIB2Iterable
from iterable.datatypes.mseed import HAS_OBSPY, MiniSEEDIterable
from iterable.datatypes.segy import HAS_SEGYIO, SEGYIterable
from iterable.exceptions import WriteNotSupportedError


class TestSEGYMissing:
    def test_id(self):
        assert SEGYIterable.id() == "segy"

    def test_import_error_when_missing(self):
        if HAS_SEGYIO:
            pytest.skip("segyio is installed")
        with pytest.raises(ImportError, match="segyio"):
            SEGYIterable(filename="x.segy")


@pytest.mark.skipif(not HAS_SEGYIO, reason="segyio not installed")
class TestSEGY:
    def test_id(self):
        assert SEGYIterable.id() == "segy"

    def test_write_raises(self, tmp_path):
        # Without a real fixture, only validate write rejection if we can open.
        # If opening fails due to invalid file, still assert WriteNotSupportedError
        # path via a stub instance is not possible; skip when open fails.
        path = tmp_path / "empty.segy"
        path.write_bytes(b"")
        try:
            src = SEGYIterable(filename=str(path))
        except Exception:
            pytest.skip("cannot open empty SEG-Y with installed segyio")
        try:
            with pytest.raises(WriteNotSupportedError):
                src.write({"trace_index": 0, "samples": []})
        finally:
            src.close()


class TestGRIB2Missing:
    def test_id(self):
        assert GRIB2Iterable.id() == "grib2"

    def test_import_error_when_missing(self):
        if HAS_GRIB:
            pytest.skip("GRIB backend is installed")
        with pytest.raises(ImportError, match="cfgrib|pygrib|eccodes"):
            GRIB2Iterable(filename="x.grib2")


@pytest.mark.skipif(not HAS_GRIB, reason="cfgrib/pygrib/eccodes not installed")
class TestGRIB2:
    def test_id(self):
        assert GRIB2Iterable.id() == "grib2"


class TestMiniSEEDMissing:
    def test_id(self):
        assert MiniSEEDIterable.id() == "mseed"

    def test_import_error_when_missing(self):
        if HAS_OBSPY:
            pytest.skip("obspy is installed")
        with pytest.raises(ImportError, match="obspy"):
            MiniSEEDIterable(filename="x.mseed")


@pytest.mark.skipif(not HAS_OBSPY, reason="obspy not installed")
class TestMiniSEED:
    def test_id(self):
        assert MiniSEEDIterable.id() == "mseed"
