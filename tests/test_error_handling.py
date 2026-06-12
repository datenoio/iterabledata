"""Tests for error handling controls."""

import json
import tempfile
import warnings
from pathlib import Path

import pytest

from iterable.exceptions import FormatParseError
from iterable.helpers.detect import open_iterable


class TestErrorPolicy:
    """Test error policy configuration."""

    def test_error_policy_raise_default(self, tmp_path):
        """Test that 'raise' is the default error policy."""
        # Create a CSV file with invalid data
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age\nJohn,30\nInvalid,row\nJane,25")

        # Default behavior should raise
        with open_iterable(str(csv_file)) as source:
            rows = list(source)
            # Should process valid rows
            assert len(rows) >= 1

    def test_error_policy_skip(self, tmp_path):
        """Test 'skip' error policy skips bad records."""
        # Create a JSONL file with invalid JSON
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"name": "John", "age": 30}\n{"invalid": json}\n{"name": "Jane", "age": 25}\n')

        rows = []
        with open_iterable(str(jsonl_file), iterableargs={"on_error": "skip"}) as source:
            for row in source:
                rows.append(row)

        # Should have processed valid rows, skipped invalid
        assert len(rows) >= 2

    def test_error_policy_warn(self, tmp_path):
        """Test 'warn' error policy logs warnings."""
        # Create a JSONL file with invalid JSON
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"name": "John", "age": 30}\n{"invalid": json}\n')

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            rows = []
            with open_iterable(str(jsonl_file), iterableargs={"on_error": "warn"}) as source:
                for row in source:
                    rows.append(row)

            # Should have warnings
            assert len(w) > 0
            assert any("Parse error" in str(warning.message) for warning in w)

    def test_error_policy_invalid(self):
        """Test that invalid error policy raises ValueError."""
        with pytest.raises(ValueError, match="Invalid 'on_error' value"):
            with open_iterable("dummy.csv", iterableargs={"on_error": "invalid"}):
                pass


class TestErrorLogging:
    """Test error logging functionality."""

    def test_error_log_file_path(self, tmp_path):
        """Test error logging to file path."""
        # Create a JSONL file with invalid JSON
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"name": "John"}\n{"invalid": json}\n')

        error_log = tmp_path / "errors.log"

        with open_iterable(
            str(jsonl_file),
            iterableargs={"on_error": "skip", "error_log": str(error_log)},
        ) as source:
            list(source)  # Process all rows

        # Check that error log was created
        assert error_log.exists()

        # Check log content
        with open(error_log) as f:
            log_lines = f.readlines()
            assert len(log_lines) > 0

            # Parse first log entry
            log_entry = json.loads(log_lines[0])
            assert "timestamp" in log_entry
            assert "filename" in log_entry
            assert "error_type" in log_entry
            assert "error_message" in log_entry

    def test_error_log_file_object(self, tmp_path):
        """Test error logging to file-like object."""
        # Create a JSONL file with invalid JSON
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"invalid": json}\n')

        error_log_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log")
        error_log_path = error_log_file.name
        error_log_file.close()

        try:
            with open(error_log_path, "w") as log_file:
                with open_iterable(
                    str(jsonl_file),
                    iterableargs={"on_error": "skip", "error_log": log_file},
                ) as source:
                    list(source)  # Process all rows

            # Check that error log was written
            with open(error_log_path) as f:
                content = f.read()
                assert len(content) > 0
        finally:
            Path(error_log_path).unlink()


class TestErrorContext:
    """Test contextual error information."""

    def test_format_parse_error_context(self):
        """Test that FormatParseError includes contextual information."""
        error = FormatParseError(
            format_id="csv",
            message="Invalid delimiter",
            filename="test.csv",
            row_number=5,
            byte_offset=1234,
            original_line="a,b,c",
        )

        assert error.filename == "test.csv"
        assert error.row_number == 5
        assert error.byte_offset == 1234
        assert error.original_line == "a,b,c"
        assert "test.csv" in str(error)
        assert "row 5" in str(error) or "5" in str(error)

    def test_error_context_in_jsonl(self, tmp_path):
        """Test that JSONL errors include context."""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"name": "John"}\n{"invalid": json}\n')

        error_log = tmp_path / "errors.log"

        with open_iterable(
            str(jsonl_file),
            iterableargs={"on_error": "skip", "error_log": str(error_log)},
        ) as source:
            list(source)

        # Check log has context
        with open(error_log) as f:
            log_entry = json.loads(f.readline())
            assert "row_number" in log_entry
            assert "original_line" in log_entry
            assert log_entry["original_line"] == '{"invalid": json}'


class TestBackwardCompatibility:
    """Test that existing code continues to work."""

    def test_default_behavior_unchanged(self, tmp_path):
        """Test that default behavior (raise) is unchanged."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age\nJohn,30\nJane,25")

        # Should work exactly as before
        with open_iterable(str(csv_file)) as source:
            rows = list(source)
            assert len(rows) == 2

    def test_no_error_handling_args(self, tmp_path):
        """Test that code without error handling args works."""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"name": "John"}\n{"name": "Jane"}\n')

        with open_iterable(str(jsonl_file)) as source:
            rows = list(source)
            assert len(rows) == 2
