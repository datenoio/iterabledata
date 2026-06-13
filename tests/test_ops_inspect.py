"""
Tests for ops.inspect module.
"""

import pytest

from iterable.ops import inspect


class TestInspect:
    def test_count_csv_file(self):
        """Test counting rows in a CSV file."""
        count = inspect.count("fixtures/2cols6rows.csv")
        assert count == 6

    def test_count_jsonl_file(self):
        """Test counting rows in a JSONL file."""
        count = inspect.count("fixtures/2cols6rows_flat.jsonl")
        assert count == 6

    def test_count_with_duckdb(self):
        """Test counting with DuckDB engine."""
        try:
            count = inspect.count("fixtures/2cols6rows.csv", engine="duckdb")
            assert count == 6
        except ImportError:
            pytest.skip("DuckDB not available")

    def test_count_iterable(self):
        """Test counting from an iterable."""
        rows = [{"a": 1}, {"a": 2}, {"a": 3}]
        count = inspect.count(rows)
        assert count == 3

    def test_count_empty(self):
        """Test counting empty dataset."""
        count = inspect.count([])
        assert count == 0

    def test_head_csv_file(self):
        """Test getting first N rows from CSV."""
        rows = list(inspect.head("fixtures/2cols6rows.csv", n=3))
        assert len(rows) == 3

    def test_head_iterable(self):
        """Test getting first N rows from iterable."""
        rows = [{"a": i} for i in range(10)]
        head_rows = list(inspect.head(rows, n=5))
        assert len(head_rows) == 5
        assert head_rows[0]["a"] == 0

    def test_head_empty(self):
        """Test head with empty dataset."""
        rows = list(inspect.head([], n=10))
        assert len(rows) == 0

    def test_tail_csv_file(self):
        """Test getting last N rows from CSV."""
        rows = inspect.tail("fixtures/2cols6rows.csv", n=3)
        assert len(rows) == 3

    def test_tail_iterable(self):
        """Test getting last N rows from iterable."""
        rows = [{"a": i} for i in range(10)]
        tail_rows = inspect.tail(rows, n=3)
        assert len(tail_rows) == 3
        assert tail_rows[0]["a"] == 7
        assert tail_rows[-1]["a"] == 9

    def test_tail_smaller_than_n(self):
        """Test tail when dataset is smaller than n."""
        rows = [{"a": i} for i in range(3)]
        tail_rows = inspect.tail(rows, n=10)
        assert len(tail_rows) == 3

    def test_tail_empty(self):
        """Test tail with empty dataset."""
        rows = inspect.tail([], n=10)
        assert len(rows) == 0

    def test_headers_csv_file(self):
        """Test getting headers from CSV file."""
        headers = inspect.headers("fixtures/2cols6rows.csv")
        assert len(headers) > 0
        assert isinstance(headers, list)

    def test_headers_iterable(self):
        """Test getting headers from iterable."""
        rows = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        headers = inspect.headers(rows)
        assert set(headers) == {"a", "b"}

    def test_headers_empty(self):
        """Test headers with empty dataset."""
        headers = inspect.headers([])
        assert headers == []

    def test_sniff_csv(self):
        """Test sniffing CSV file."""
        info = inspect.sniff("fixtures/2cols6rows.csv")
        assert "format" in info
        assert info["format"] == "csv"
        assert "encoding" in info

    def test_sniff_jsonl(self):
        """Test sniffing JSONL file."""
        info = inspect.sniff("fixtures/2cols6rows_flat.jsonl")
        assert "format" in info
        assert info["format"] == "jsonl"

    def test_analyze_csv(self):
        """Test analyzing CSV dataset."""
        analysis = inspect.analyze("fixtures/2cols6rows.csv", sample_size=100)
        assert "fields" in analysis
        assert "row_count" in analysis
        assert "structure" in analysis
        assert len(analysis["fields"]) > 0

    def test_analyze_iterable(self):
        """Test analyzing iterable dataset."""
        rows = [{"a": 1, "b": "test"}, {"a": 2, "b": "test2"}]
        analysis = inspect.analyze(rows)
        assert "fields" in analysis
        assert "a" in analysis["fields"]
        assert "b" in analysis["fields"]
        assert analysis["fields"]["a"]["type"] == "int"
        assert analysis["fields"]["b"]["type"] == "str"

    def test_analyze_empty(self):
        """Test analyze with empty dataset."""
        analysis = inspect.analyze([])
        assert analysis["row_count"] == 0
        assert len(analysis["fields"]) == 0
