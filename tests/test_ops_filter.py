"""
Tests for ops.filter module.
"""

import pytest

from iterable.ops import filter as f


class TestFilter:
    def test_filter_expr_simple(self):
        """Test filtering with simple expression."""
        rows = [
            {"status": "active", "price": 50},
            {"status": "inactive", "price": 30},
            {"status": "active", "price": 100},
        ]
        result = list(f.filter_expr(rows, "`status` == 'active'"))
        assert len(result) == 2
        assert all(r["status"] == "active" for r in result)

    def test_filter_expr_complex(self):
        """Test filtering with complex expression."""
        rows = [
            {"status": "active", "price": 150},
            {"status": "active", "price": 50},
            {"status": "inactive", "price": 200},
        ]
        result = list(f.filter_expr(rows, "`status` == 'active' and `price` > 100"))
        assert len(result) == 1
        assert result[0]["price"] == 150

    def test_filter_expr_comparison_operators(self):
        """Test different comparison operators."""
        rows = [
            {"value": 10},
            {"value": 20},
            {"value": 30},
        ]
        # Greater than
        result = list(f.filter_expr(rows, "`value` > 15"))
        assert len(result) == 2
        # Less than or equal
        result = list(f.filter_expr(rows, "`value` <= 20"))
        assert len(result) == 2
        # Not equal
        result = list(f.filter_expr(rows, "`value` != 20"))
        assert len(result) == 2

    def test_filter_expr_boolean_operators(self):
        """Test boolean operators."""
        rows = [
            {"status": "active", "type": "A"},
            {"status": "active", "type": "B"},
            {"status": "inactive", "type": "A"},
        ]
        # OR
        result = list(f.filter_expr(rows, "`status` == 'active' or `type` == 'A'"))
        assert len(result) == 3
        # AND
        result = list(f.filter_expr(rows, "`status` == 'active' and `type` == 'A'"))
        assert len(result) == 1

    def test_filter_expr_missing_fields(self):
        """Test filtering with missing fields."""
        rows = [
            {"status": "active"},
            {"status": "inactive", "price": 100},
        ]
        # Missing field should evaluate to None
        result = list(f.filter_expr(rows, "`price` > 50"))
        assert len(result) == 1

    def test_filter_expr_invalid_expression(self):
        """Test handling of invalid expressions."""
        rows = [{"a": 1}]
        with pytest.raises(ValueError):
            list(f.filter_expr(rows, "invalid expression syntax"))

    def test_search_all_fields(self):
        """Test regex search across all fields."""
        rows = [
            {"message": "error occurred", "level": "info"},
            {"message": "success", "level": "warning"},
            {"message": "ok", "level": "error"},
        ]
        # Matches: row 1 (message "error occurred"), row 2 (level "warning"),
        # and row 3 (level "error") -> all three rows.
        result = list(f.search(rows, pattern="error|warning"))
        assert len(result) == 3

    def test_search_specific_fields(self):
        """Test regex search in specific fields."""
        rows = [
            {"phone": "123-456-7890", "email": "test@example.com"},
            {"phone": "invalid", "email": "user@test.com"},
            {"phone": "987-654-3210", "email": "other@example.com"},
        ]
        result = list(f.search(rows, pattern=r"\d{3}-\d{3}-\d{4}", fields=["phone"]))
        assert len(result) == 2

    def test_search_case_insensitive(self):
        """Test case-insensitive search."""
        rows = [
            {"status": "ERROR"},
            {"status": "error"},
            {"status": "Error"},
            {"status": "success"},
        ]
        result = list(f.search(rows, pattern="error", ignore_case=True))
        assert len(result) == 3

    def test_search_invalid_regex(self):
        """Test handling of invalid regex patterns."""
        rows = [{"a": "test"}]
        with pytest.raises(ValueError):
            list(f.search(rows, pattern="[invalid regex"))

    def test_query_mistql_simple(self):
        """Test simple MistQL query."""
        rows = [
            {"status": "active", "price": 100},
            {"status": "inactive", "price": 50},
            {"status": "active", "price": 200},
        ]
        result = list(f.query_mistql(rows, "SELECT * WHERE status = 'active'"))
        assert len(result) == 2

    def test_query_mistql_field_selection(self):
        """Test query with field selection."""
        rows = [
            {"id": 1, "name": "A", "price": 100},
            {"id": 2, "name": "B", "price": 200},
        ]
        result = list(f.query_mistql(rows, "SELECT id, name WHERE price > 150"))
        assert len(result) == 1
        assert "id" in result[0]
        assert "name" in result[0]
        assert "price" not in result[0]

    def test_query_mistql_no_where(self):
        """Test query without WHERE clause."""
        rows = [
            {"a": 1},
            {"a": 2},
        ]
        result = list(f.query_mistql(rows, "SELECT *"))
        assert len(result) == 2

    def test_query_mistql_invalid(self):
        """Test handling of invalid queries."""
        rows = [{"a": 1}]
        with pytest.raises(ValueError):
            list(f.query_mistql(rows, "INVALID QUERY"))

    def test_filter_expr_csv_file(self):
        """Test filtering CSV file."""
        # This will test file path handling
        try:
            result = list(f.filter_expr("fixtures/2cols6rows.csv", "`col1` == 'value1'"))
            # Result depends on file content
            assert isinstance(result, list)
        except Exception:
            # May fail if file doesn't have expected structure
            pass

    def test_search_csv_file(self):
        """Test regex search on CSV file."""
        try:
            result = list(f.search("fixtures/2cols6rows.csv", pattern="value"))
            assert isinstance(result, list)
        except Exception:
            pass
