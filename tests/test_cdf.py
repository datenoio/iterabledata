"""Tests for NASA Common Data Format (CDF) support."""

import os
import tempfile

import pytest

pytest.importorskip("spacepy", reason="spacepy (CDF) not installed")

from iterable.helpers.detect import detect_file_type, open_iterable


class TestCDFDetection:
    """Detection and open_iterable for CDF."""

    def test_detect_cdf_extension(self):
        """Detect format from .cdf extension."""
        result = detect_file_type("data.cdf")
        assert result["success"] is True
        assert result["datatype"] is not None
        assert result["datatype"].__name__ == "CDFIterable"
        assert result["confidence"] == 1.0

    def test_open_iterable_cdf_auto_detect(self):
        """open_iterable on .cdf path uses CDFIterable (requires spacepy)."""
        with tempfile.NamedTemporaryFile(suffix=".cdf", delete=False) as tmp:
            path = tmp.name
        try:
            # Create minimal empty CDF; spacepy may create one or we skip if no CDF lib
            try:
                from spacepy import pycdf

                with pycdf.CDF(path, "") as cdf:
                    cdf["x"] = [1, 2, 3]
            except Exception:
                pytest.skip("NASA CDF C library not available or cannot create CDF")
            with open_iterable(path) as it:
                assert it.__class__.__name__ == "CDFIterable"
                rows = list(it)
                assert len(rows) == 3
                assert rows[0]["x"] == 1
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestCDFMissingDependency:
    """When CDF dependency is missing, clear error is raised."""

    def test_import_error_message(self):
        """CDFIterable raises ImportError with install hint when spacepy missing."""
        try:
            from iterable.datatypes.cdf import CDFIterable  # noqa: F401
        except ImportError as e:
            assert "iterabledata[cdf]" in str(e) or "spacepy" in str(e).lower()
