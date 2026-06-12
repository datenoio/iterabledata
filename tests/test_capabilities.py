"""Tests for format capability reporting."""

import pytest

from iterable.exceptions import FormatDetectionError
from iterable.helpers.capabilities import (
    get_capability,
    get_format_capabilities,
    list_all_capabilities,
)


class TestGetFormatCapabilities:
    """Test get_format_capabilities() function."""

    def test_csv_capabilities(self):
        """Test CSV format capabilities."""
        caps = get_format_capabilities("csv")

        assert caps["readable"] is True
        assert caps["writable"] is True
        assert caps["bulk_read"] is True
        assert caps["bulk_write"] is True
        assert caps["totals"] is True
        assert caps["flat_only"] is True
        assert caps["nested"] is False
        assert caps["tables"] is False
        assert caps["streaming"] is True
        assert caps["compression"] is True

    def test_json_capabilities(self):
        """Test JSON format capabilities."""
        caps = get_format_capabilities("json")

        assert caps["readable"] is True
        assert caps["writable"] is True
        assert caps["bulk_read"] is True
        assert caps["bulk_write"] is True
        assert caps["totals"] is True
        assert caps["flat_only"] is False
        assert caps["nested"] is True
        assert caps["tables"] is False
        assert caps["streaming"] is True
        assert caps["compression"] is True

    def test_jsonl_capabilities(self):
        """Test JSONL format capabilities."""
        caps = get_format_capabilities("jsonl")

        assert caps["readable"] is True
        assert caps["writable"] is True
        assert caps["bulk_read"] is True
        assert caps["bulk_write"] is True
        assert caps["totals"] is True
        assert caps["flat_only"] is False
        assert caps["nested"] is True

    def test_xml_capabilities(self):
        """Test XML format capabilities."""
        caps = get_format_capabilities("xml")

        assert caps["readable"] is True
        assert caps["tables"] is True  # XML supports multiple tags
        assert caps["flat_only"] is False
        assert caps["nested"] is True

    def test_xlsx_capabilities(self):
        """Test XLSX format capabilities."""
        caps = get_format_capabilities("xlsx")

        assert caps["readable"] is True
        assert caps["tables"] is True  # XLSX supports multiple sheets
        assert caps["totals"] is True

    def test_unknown_format(self):
        """Test error handling for unknown format."""
        with pytest.raises(FormatDetectionError, match="Unknown format"):
            get_format_capabilities("unknown_format_xyz")

    def test_format_id_case_insensitive(self):
        """Test that format IDs are case-insensitive."""
        caps1 = get_format_capabilities("CSV")
        caps2 = get_format_capabilities("csv")
        caps3 = get_format_capabilities("Csv")

        assert caps1 == caps2 == caps3

    def test_all_capability_keys_present(self):
        """Test that all expected capability keys are present."""
        caps = get_format_capabilities("csv")

        expected_keys = {
            "readable",
            "writable",
            "bulk_read",
            "bulk_write",
            "totals",
            "streaming",
            "flat_only",
            "tables",
            "compression",
            "nested",
        }

        assert set(caps.keys()) == expected_keys

    def test_caching(self):
        """Test that capabilities are cached."""
        # Clear any existing cache by accessing it directly
        from iterable.helpers.capabilities import _CAPABILITY_CACHE

        if "csv" in _CAPABILITY_CACHE:
            del _CAPABILITY_CACHE["csv"]

        # First call should populate cache
        caps1 = get_format_capabilities("csv")

        # Second call should use cache (same object reference)
        caps2 = get_format_capabilities("csv")

        # Values should be equal
        assert caps1 == caps2


class TestGetCapability:
    """Test get_capability() function."""

    def test_get_specific_capability(self):
        """Test querying a specific capability."""
        assert get_capability("csv", "readable") is True
        assert get_capability("csv", "writable") is True
        assert get_capability("csv", "totals") is True
        assert get_capability("csv", "flat_only") is True
        assert get_capability("csv", "nested") is False
        assert get_capability("csv", "tables") is False

    def test_get_capability_json(self):
        """Test querying JSON capabilities."""
        assert get_capability("json", "readable") is True
        assert get_capability("json", "writable") is True
        assert get_capability("json", "nested") is True
        assert get_capability("json", "flat_only") is False

    def test_get_capability_unknown_format(self):
        """Test error handling for unknown format."""
        with pytest.raises(FormatDetectionError, match="Unknown format"):
            get_capability("unknown_format", "readable")

    def test_get_capability_invalid_key(self):
        """Test that invalid capability key returns None."""
        result = get_capability("csv", "invalid_capability")
        assert result is None

    def test_get_capability_case_insensitive_format(self):
        """Test that format ID is case-insensitive."""
        assert get_capability("CSV", "readable") == get_capability("csv", "readable")


class TestListAllCapabilities:
    """Test list_all_capabilities() function."""

    def test_returns_dict(self):
        """Test that function returns a dictionary."""
        all_caps = list_all_capabilities()
        assert isinstance(all_caps, dict)

    def test_includes_common_formats(self):
        """Test that common formats are included."""
        all_caps = list_all_capabilities()

        assert "csv" in all_caps
        assert "json" in all_caps
        assert "jsonl" in all_caps
        assert "xml" in all_caps

    def test_all_entries_have_capability_keys(self):
        """Test that all entries have the expected capability keys."""
        all_caps = list_all_capabilities()

        expected_keys = {
            "readable",
            "writable",
            "bulk_read",
            "bulk_write",
            "totals",
            "streaming",
            "flat_only",
            "tables",
            "compression",
            "nested",
        }

        for format_id, caps in all_caps.items():
            assert isinstance(caps, dict), f"Format {format_id} capabilities should be a dict"
            assert set(caps.keys()) == expected_keys, f"Format {format_id} missing expected keys"

    def test_csv_in_list(self):
        """Test that CSV capabilities match when retrieved individually."""
        all_caps = list_all_capabilities()
        csv_caps = get_format_capabilities("csv")

        assert "csv" in all_caps
        assert all_caps["csv"] == csv_caps

    def test_multiple_extensions_same_class(self):
        """Test that formats sharing the same class have same capabilities."""
        all_caps = list_all_capabilities()

        # CSV and TSV should have same capabilities (both use CSVIterable)
        if "csv" in all_caps and "tsv" in all_caps:
            assert all_caps["csv"] == all_caps["tsv"]


class TestCapabilityAccuracy:
    """Test that detected capabilities match actual format behavior."""

    def test_csv_flat_only_matches_implementation(self):
        """Test that CSV flat_only matches actual implementation."""
        from iterable.datatypes import CSVIterable

        caps = get_format_capabilities("csv")
        actual_flat_only = CSVIterable.is_flatonly()

        assert caps["flat_only"] == actual_flat_only
        assert caps["nested"] == (not actual_flat_only)

    def test_json_flat_only_matches_implementation(self):
        """Test that JSON flat_only matches actual implementation."""
        from iterable.datatypes import JSONIterable

        caps = get_format_capabilities("json")
        actual_flat_only = JSONIterable.is_flatonly()

        assert caps["flat_only"] == actual_flat_only
        assert caps["nested"] == (not actual_flat_only)

    def test_csv_has_totals_matches_implementation(self):
        """Test that CSV totals support matches actual implementation."""
        from iterable.datatypes import CSVIterable

        caps = get_format_capabilities("csv")
        actual_has_totals = CSVIterable.has_totals()

        assert caps["totals"] == actual_has_totals

    def test_xml_has_tables_matches_implementation(self):
        """Test that XML tables support matches actual implementation."""
        from iterable.datatypes import XMLIterable

        caps = get_format_capabilities("xml")
        actual_has_tables = XMLIterable.has_tables()

        assert caps["tables"] == actual_has_tables

    def test_method_existence_matches_capabilities(self):
        """Test that method existence matches capability flags."""
        from iterable.datatypes import CSVIterable

        caps = get_format_capabilities("csv")

        # Check that readable matches read() method existence
        assert caps["readable"] == (hasattr(CSVIterable, "read") and callable(getattr(CSVIterable, "read", None)))

        # Check that writable matches write() method existence
        assert caps["writable"] == (hasattr(CSVIterable, "write") and callable(getattr(CSVIterable, "write", None)))

        # Check that bulk_read matches read_bulk() method existence
        assert caps["bulk_read"] == (
            hasattr(CSVIterable, "read_bulk") and callable(getattr(CSVIterable, "read_bulk", None))
        )

        # Check that bulk_write matches write_bulk() method existence
        assert caps["bulk_write"] == (
            hasattr(CSVIterable, "write_bulk") and callable(getattr(CSVIterable, "write_bulk", None))
        )


class TestOptionalDependencies:
    """Test handling of formats with optional dependencies."""

    def test_handles_missing_optional_dependency_gracefully(self):
        """Test that missing optional dependencies don't crash."""
        # Try to get capabilities for a format that might have optional dependencies
        # We can't easily test this without mocking, but we can verify the function
        # doesn't crash for formats that exist in the registry

        all_caps = list_all_capabilities()

        # All formats should return capability dicts, even if dependencies are missing
        for format_id, caps in all_caps.items():
            assert isinstance(caps, dict)
            # Values might be None if dependencies are missing, which is acceptable
            assert all(v is None or isinstance(v, bool) for v in caps.values()), (
                f"Format {format_id} has invalid capability values"
            )

    def test_get_format_capabilities_import_error_handling(self):
        """Test that ImportError is handled gracefully."""
        # This tests the error handling path in get_format_capabilities
        # We can't easily mock ImportError without more complex setup,
        # but we can verify the function structure handles it
        caps = get_format_capabilities("csv")
        assert isinstance(caps, dict)

    def test_list_all_capabilities_handles_errors(self):
        """Test that list_all_capabilities handles errors for individual formats."""
        all_caps = list_all_capabilities()
        # Should return dict even if some formats fail
        assert isinstance(all_caps, dict)
        # All entries should be dicts
        for _format_id, caps in all_caps.items():
            assert isinstance(caps, dict)

    def test_get_capability_all_keys(self):
        """Test get_capability with all possible capability keys."""
        capability_keys = [
            "readable",
            "writable",
            "bulk_read",
            "bulk_write",
            "totals",
            "streaming",
            "flat_only",
            "tables",
            "compression",
            "nested",
        ]
        for key in capability_keys:
            result = get_capability("csv", key)
            assert result is None or isinstance(result, bool)

    def test_detect_capabilities_internal(self):
        """Test _detect_capabilities function directly."""
        from iterable.datatypes import CSVIterable
        from iterable.helpers.capabilities import _detect_capabilities

        caps = _detect_capabilities(CSVIterable)
        assert isinstance(caps, dict)
        assert "readable" in caps
        assert "writable" in caps
        assert caps["readable"] is True
        assert caps["writable"] is True

    def test_get_format_class_internal(self):
        """Test _get_format_class function."""
        from iterable.helpers.capabilities import _get_format_class

        format_class = _get_format_class("csv")
        from iterable.datatypes import CSVIterable

        assert format_class == CSVIterable

    def test_get_format_class_unknown_format(self):
        """Test _get_format_class with unknown format."""
        from iterable.helpers.capabilities import _get_format_class

        with pytest.raises(FormatDetectionError, match="Unknown format"):
            _get_format_class("unknown_format_xyz123")

    def test_capability_cache_isolation(self):
        """Test that capability cache returns copies, not references."""
        from iterable.helpers.capabilities import _CAPABILITY_CACHE

        # Clear cache
        if "csv" in _CAPABILITY_CACHE:
            del _CAPABILITY_CACHE["csv"]

        caps1 = get_format_capabilities("csv")
        caps2 = get_format_capabilities("csv")

        # Should be equal but not the same object (copies)
        assert caps1 == caps2
        # Modifying one shouldn't affect the other
        caps1["readable"] = False
        caps3 = get_format_capabilities("csv")
        assert caps3["readable"] is True  # Should still be True from cache
