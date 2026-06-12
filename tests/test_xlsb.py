"""Tests for XLSB format (pyxlsb)."""

import os
import tempfile

import pytest

try:
    from pyxlsb import open_workbook  # noqa: F401

    HAS_PYXLSB = True
except ImportError:
    HAS_PYXLSB = False

from iterable.datatypes.xlsb import XLSBIterable


@pytest.mark.skipif(not HAS_PYXLSB, reason="pyxlsb not installed")
class TestXLSB:
    def test_xlsb_id(self):
        assert XLSBIterable.id() == "xlsb"

    def test_xlsb_flatonly(self):
        assert XLSBIterable.is_flatonly()

    def test_xlsb_has_tables(self):
        assert XLSBIterable.has_tables()

    def test_xlsb_requires_filename(self):
        """XLSB requires filename; stream is not supported."""
        with pytest.raises(ValueError):
            XLSBIterable(filename=None, mode="r")


@pytest.mark.skipif(HAS_PYXLSB, reason="only run when pyxlsb is not installed")
def test_xlsb_import_error_without_pyxlsb():
    """Without pyxlsb, XLSBIterable raises ImportError with install hint."""
    with tempfile.NamedTemporaryFile(suffix=".xlsb", delete=False) as f:
        path = f.name
    try:
        with pytest.raises(ImportError) as exc_info:
            XLSBIterable(path, mode="r")
        assert "iterabledata[xlsb]" in str(exc_info.value) or "pyxlsb" in str(exc_info.value).lower()
    finally:
        os.unlink(path)
