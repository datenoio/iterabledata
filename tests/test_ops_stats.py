"""
Tests for ops.stats module.
"""

from iterable.ops import stats


class TestStats:
    def test_compute_csv(self):
        """Test computing statistics for CSV file."""
        summary = stats.compute("fixtures/2cols6rows.csv")
        assert isinstance(summary, dict)
        assert len(summary) > 0

    def test_compute_iterable(self):
        """Test computing statistics for iterable."""
        rows = [
            {"value": 1, "name": "a"},
            {"value": 2, "name": "b"},
            {"value": 3, "name": "c"},
        ]
        summary = stats.compute(rows)
        assert "value" in summary
        assert "name" in summary
        assert summary["value"]["count"] == 3
        assert summary["value"]["min"] == 1
        assert summary["value"]["max"] == 3
        assert summary["value"]["mean"] == 2.0

    def test_compute_with_nulls(self):
        """Test computing statistics with null values."""
        rows = [
            {"value": 1},
            {"value": None},
            {"value": 3},
        ]
        summary = stats.compute(rows)
        assert summary["value"]["count"] == 2
        assert summary["value"]["null_count"] == 1

    def test_compute_flatten_nested(self):
        rows = [
            {"capital_city": {"name": "Paris", "lat": 48.8}},
            {"capital_city": {"name": "Tokyo", "lat": 35.6}},
            {"capital_city": None},
        ]
        summary = stats.compute(rows, flatten_nested=True)
        assert "capital_city" in summary
        assert "capital_city.name" in summary
        assert "capital_city.lat" in summary
        assert summary["capital_city.name"]["count"] == 2
        assert summary["capital_city.name"]["null_count"] == 1
        assert summary["capital_city.lat"]["min"] == 35.6
        assert summary["capital_city.lat"]["max"] == 48.8

    def test_compute_flatten_array_of_dicts_counts_all_elements(self):
        rows = [
            {"languages": [{"code": "rus"}, {"code": "tgk"}]},
            {"languages": [{"code": "eng"}]},
            {"languages": []},
        ]
        summary = stats.compute(rows, flatten_nested=True)
        assert summary["languages.code"]["count"] == 3
        assert summary["languages.code"]["unique_count"] == 3
        assert summary["languages.code"]["null_count"] == 1

    def test_compute_without_flatten_keeps_parent_only(self):
        rows = [{"capital_city": {"name": "Paris", "lat": 48.8}}]
        summary = stats.compute(rows)
        assert "capital_city" in summary
        assert "capital_city.name" not in summary

    def test_frequency_single_field(self):
        """Test frequency analysis for single field."""
        rows = [
            {"status": "active"},
            {"status": "inactive"},
            {"status": "active"},
        ]
        freq = stats.frequency(rows, fields=["status"])
        assert "status" in freq
        assert freq["status"]["active"] == 2
        assert freq["status"]["inactive"] == 1

    def test_frequency_multiple_fields(self):
        """Test frequency analysis for multiple fields."""
        rows = [
            {"status": "active", "type": "A"},
            {"status": "inactive", "type": "B"},
            {"status": "active", "type": "A"},
        ]
        freq = stats.frequency(rows, fields=["status", "type"])
        assert "status" in freq
        assert "type" in freq
        assert freq["status"]["active"] == 2

    def test_frequency_with_limit(self):
        """Test frequency analysis with limit."""
        rows = [{"value": i % 3} for i in range(10)]
        freq = stats.frequency(rows, fields=["value"], limit=2)
        assert len(freq["value"]) <= 2

    def test_uniq_by_field(self):
        """Test finding unique rows by field."""
        rows = [
            {"email": "a@test.com", "name": "A"},
            {"email": "b@test.com", "name": "B"},
            {"email": "a@test.com", "name": "C"},  # Duplicate email
        ]
        unique = list(stats.uniq(rows, fields=["email"]))
        assert len(unique) == 2

    def test_uniq_values_only(self):
        """Test getting unique values only."""
        rows = [
            {"email": "a@test.com"},
            {"email": "b@test.com"},
            {"email": "a@test.com"},
        ]
        unique = list(stats.uniq(rows, fields=["email"], values_only=True))
        assert len(unique) == 2
        assert "a@test.com" in unique
        assert "b@test.com" in unique

    def test_uniq_with_count(self):
        """Test unique with count."""
        rows = [
            {"email": "a@test.com"},
            {"email": "b@test.com"},
            {"email": "a@test.com"},
        ]
        result = stats.uniq(rows, fields=["email"], include_count=True)
        assert isinstance(result, dict)
        # Note: This is a simplified test - the actual implementation may differ

    def test_compute_string_stats(self):
        """Test computing statistics for string fields."""
        rows = [
            {"name": "a"},
            {"name": "ab"},
            {"name": "abc"},
        ]
        summary = stats.compute(rows)
        assert "name" in summary
        assert "min_length" in summary["name"]
        assert "max_length" in summary["name"]
        assert summary["name"]["min_length"] == 1
        assert summary["name"]["max_length"] == 3
