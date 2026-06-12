"""Comprehensive edge case tests for IterableData.

These tests cover various edge cases and boundary conditions that might
not be covered by standard functionality tests.

Run with: pytest tests/test_edge_cases.py -v
"""

import io

import pytest

from iterable.datatypes.csv import CSVIterable
from iterable.exceptions import (
    FormatDetectionError,
    FormatParseError,
    ReadError,
    WriteNotSupportedError,
)
from iterable.helpers.detect import open_iterable


class TestEmptyFiles:
    """Test handling of empty files"""

    def test_empty_csv_file(self, tmp_path):
        """Test reading from completely empty CSV file"""
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("")

        with open_iterable(empty_file) as source:
            # Should raise StopIteration immediately
            with pytest.raises(StopIteration):
                source.read()

    def test_empty_csv_file_with_header_only(self, tmp_path):
        """Test reading from CSV file with only header"""
        header_only = tmp_path / "header_only.csv"
        header_only.write_text("id,name\n")

        with open_iterable(header_only) as source:
            with pytest.raises(StopIteration):
                source.read()

    def test_empty_jsonl_file(self, tmp_path):
        """Test reading from empty JSONL file"""
        empty_file = tmp_path / "empty.jsonl"
        empty_file.write_text("")

        with open_iterable(empty_file) as source:
            with pytest.raises(StopIteration):
                source.read()

    def test_empty_json_file(self, tmp_path):
        """Test reading from empty JSON file"""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("")

        with open_iterable(empty_file) as source:
            # Empty JSON should raise an error
            with pytest.raises((ValueError, FormatParseError, ReadError)):
                source.read()

    def test_write_to_empty_file(self, tmp_path):
        """Test writing to an empty file path"""
        output_file = tmp_path / "output.csv"
        data = [{"id": 1, "name": "test"}]

        with open_iterable(output_file, "w") as dest:
            dest.write_bulk(data)

        # Verify file was created and has content
        assert output_file.exists()
        assert output_file.stat().st_size > 0


class TestMissingFiles:
    """Test handling of missing files"""

    def test_read_nonexistent_file(self, tmp_path):
        """Test reading from non-existent file"""
        nonexistent = tmp_path / "nonexistent.csv"

        with pytest.raises((FileNotFoundError, OSError)):
            with open_iterable(nonexistent) as source:
                source.read()

    def test_write_to_nonexistent_directory(self, tmp_path):
        """Test writing to non-existent directory"""
        nonexistent_dir = tmp_path / "nonexistent" / "file.csv"

        with pytest.raises((FileNotFoundError, OSError)):
            with open_iterable(nonexistent_dir, "w") as dest:
                dest.write({"id": 1})


class TestInvalidData:
    """Test handling of invalid or malformed data"""

    def test_csv_malformed_row(self, tmp_path):
        """Test CSV with malformed row"""
        malformed_file = tmp_path / "malformed.csv"
        malformed_file.write_text("id,name\n1,valid\ninvalid,row,with,too,many,commas\n2,valid\n")

        with open_iterable(malformed_file, options={"on_error": "skip"}) as source:
            rows = list(source)
            # Should skip malformed row and read valid ones
            assert len(rows) >= 2

    def test_jsonl_invalid_json(self, tmp_path):
        """Test JSONL with invalid JSON line"""
        invalid_file = tmp_path / "invalid.jsonl"
        invalid_file.write_text('{"id": 1}\ninvalid json line\n{"id": 2}\n')

        with open_iterable(invalid_file, options={"on_error": "skip"}) as source:
            rows = list(source)
            # Should skip invalid line and read valid ones
            assert len(rows) >= 2

    def test_csv_unescaped_quotes(self, tmp_path):
        """Test CSV with unescaped quotes"""
        unescaped_file = tmp_path / "unescaped.csv"
        unescaped_file.write_text('id,name\n1,"quoted,value"\n2,normal\n')

        with open_iterable(unescaped_file) as source:
            rows = list(source)
            assert len(rows) == 2

    def test_jsonl_truncated_line(self, tmp_path):
        """Test JSONL with truncated JSON line"""
        truncated_file = tmp_path / "truncated.jsonl"
        truncated_file.write_text('{"id": 1, "name": "test"}\n{"id": 2, "name": "incomplete\n')

        with open_iterable(truncated_file, options={"on_error": "skip"}) as source:
            rows = list(source)
            # Should handle truncated line gracefully
            assert len(rows) >= 1


class TestBoundaryConditions:
    """Test boundary conditions and limits"""

    def test_single_row_file(self, tmp_path):
        """Test file with only one row"""
        single_row = tmp_path / "single.csv"
        single_row.write_text("id,name\n1,test\n")

        with open_iterable(single_row) as source:
            rows = list(source)
            assert len(rows) == 1
            assert rows[0]["id"] == "1"

    def test_very_long_line(self, tmp_path):
        """Test file with very long line"""
        long_line_file = tmp_path / "long_line.csv"
        long_value = "x" * 100000  # 100KB value
        long_line_file.write_text(f"id,value\n1,{long_value}\n")

        with open_iterable(long_line_file) as source:
            row = source.read()
            assert len(row["value"]) == 100000

    def test_many_columns(self, tmp_path):
        """Test CSV with many columns"""
        many_cols_file = tmp_path / "many_cols.csv"
        header = ",".join([f"col{i}" for i in range(100)])
        row = ",".join([str(i) for i in range(100)])
        many_cols_file.write_text(f"{header}\n{row}\n")

        with open_iterable(many_cols_file) as source:
            row_data = source.read()
            assert len(row_data) == 100

    def test_unicode_characters(self, tmp_path):
        """Test file with various Unicode characters"""
        unicode_file = tmp_path / "unicode.csv"
        unicode_file.write_text("id,name\n1,测试\n2,🚀\n3,ñáéíóú\n")

        with open_iterable(unicode_file) as source:
            rows = list(source)
            assert len(rows) == 3
            assert rows[0]["name"] == "测试"
            assert rows[1]["name"] == "🚀"
            assert rows[2]["name"] == "ñáéíóú"

    def test_special_characters_in_data(self, tmp_path):
        """Test file with special characters"""
        special_file = tmp_path / "special.csv"
        special_file.write_text('id,value\n1,"line1\nline2"\n2,"tab\there"\n3,"quote""here"\n')

        with open_iterable(special_file) as source:
            rows = list(source)
            assert len(rows) == 3


class TestNoneAndNullValues:
    """Test handling of None and null values"""

    def test_csv_with_empty_fields(self, tmp_path):
        """Test CSV with empty fields"""
        empty_fields = tmp_path / "empty_fields.csv"
        empty_fields.write_text("id,name,value\n1,,3\n,test,5\n7,eight,\n")

        with open_iterable(empty_fields) as source:
            rows = list(source)
            assert len(rows) == 3
            # Empty fields should be empty strings or None
            assert rows[0]["name"] in ("", None)

    def test_jsonl_with_null_values(self, tmp_path):
        """Test JSONL with null values"""
        import json

        null_file = tmp_path / "null.jsonl"
        with null_file.open("w") as f:
            f.write(json.dumps({"id": 1, "value": None}) + "\n")
            f.write(json.dumps({"id": 2, "value": "test"}) + "\n")

        with open_iterable(null_file) as source:
            rows = list(source)
            assert len(rows) == 2
            assert rows[0]["value"] is None
            assert rows[1]["value"] == "test"


class TestFilePermissions:
    """Test handling of file permission issues"""

    def test_read_only_file_read(self, tmp_path):
        """Test reading from read-only file"""
        read_only = tmp_path / "readonly.csv"
        read_only.write_text("id,name\n1,test\n")
        read_only.chmod(0o444)  # Read-only

        try:
            with open_iterable(read_only) as source:
                rows = list(source)
                assert len(rows) == 1
        finally:
            # Restore permissions for cleanup
            read_only.chmod(0o644)

    def test_read_only_file_write(self, tmp_path):
        """Test writing to read-only file should fail"""
        read_only = tmp_path / "readonly.csv"
        read_only.write_text("id,name\n1,test\n")
        read_only.chmod(0o444)  # Read-only

        try:
            with pytest.raises((PermissionError, OSError)):
                with open_iterable(read_only, "w") as dest:
                    dest.write({"id": 2, "name": "new"})
        finally:
            # Restore permissions for cleanup
            read_only.chmod(0o644)


class TestStreamEdgeCases:
    """Test edge cases with streams"""

    def test_closed_stream(self):
        """Test reading from closed stream"""
        stream = io.StringIO("id,name\n1,test\n")
        stream.close()

        with pytest.raises((ValueError, OSError)):
            with open_iterable(stream=stream) as source:
                source.read()

    def test_non_seekable_stream_reset(self):
        """Test reset on non-seekable stream"""

        # Create a stream that doesn't support seek
        class NonSeekableStream(io.StringIO):
            def seekable(self):
                return False

        stream = NonSeekableStream("id,name\n1,test\n2,test2\n")

        with open_iterable(stream=stream) as source:
            first_row = source.read()
            assert first_row is not None

            # Reset should raise error for non-seekable stream
            with pytest.raises(ReadError, match="not seekable"):
                source.reset()

    def test_empty_stream(self):
        """Test reading from empty stream"""
        stream = io.StringIO("")

        with open_iterable(stream=stream) as source:
            with pytest.raises(StopIteration):
                source.read()


class TestFactoryMethodEdgeCases:
    """Test edge cases with factory methods"""

    def test_from_file_nonexistent(self, tmp_path):
        """Test from_file with non-existent file"""
        nonexistent = tmp_path / "nonexistent.csv"

        with pytest.raises((FileNotFoundError, OSError)):
            CSVIterable.from_file(str(nonexistent))

    def test_from_file_empty_path(self):
        """Test from_file with empty path"""
        with pytest.raises((ValueError, FileNotFoundError)):
            CSVIterable.from_file("")

    def test_from_stream_none(self):
        """Test from_stream with None"""
        with pytest.raises((ValueError, TypeError)):
            CSVIterable.from_stream(None)  # type: ignore

    def test_from_codec_none(self):
        """Test from_codec with None"""
        with pytest.raises((ValueError, TypeError)):
            CSVIterable.from_codec(None)  # type: ignore


class TestInitializationEdgeCases:
    """Test edge cases in initialization"""

    def test_init_no_source(self):
        """Test initialization with no source provided"""
        with pytest.raises(ValueError, match="requires filename, stream, or codec"):
            CSVIterable()

    def test_init_multiple_sources(self):
        """Test initialization with multiple sources (should fail)"""
        stream = io.StringIO("id,name\n1,test\n")

        with pytest.raises(ValueError, match="exactly one source"):
            CSVIterable(filename="test.csv", stream=stream)

    def test_init_invalid_options(self, tmp_path):
        """Test initialization with invalid options"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test\n")

        # Try to override protected attribute
        with pytest.raises(ValueError, match="Cannot override protected attribute"):
            CSVIterable(
                filename=str(test_file),
                options={"stype": "invalid"},  # stype is protected
            )

    def test_init_invalid_error_policy(self, tmp_path):
        """Test initialization with invalid error policy"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test\n")

        with pytest.raises(ValueError, match="Invalid 'on_error' value"):
            CSVIterable(filename=str(test_file), options={"on_error": "invalid_policy"})


class TestBulkOperationEdgeCases:
    """Test edge cases in bulk operations"""

    def test_read_bulk_zero(self, tmp_path):
        """Test read_bulk with zero size"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test\n2,test2\n")

        with open_iterable(test_file) as source:
            chunk = source.read_bulk(num=0)
            assert len(chunk) == 0

    def test_read_bulk_negative(self, tmp_path):
        """Test read_bulk with negative size"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test\n")

        with open_iterable(test_file) as source:
            # Should handle negative gracefully (might return empty or raise error)
            try:
                chunk = source.read_bulk(num=-1)
                # If it doesn't raise, should return empty or handle gracefully
                assert isinstance(chunk, list)
            except (ValueError, TypeError):
                # Raising error is also acceptable
                pass

    def test_read_bulk_larger_than_file(self, tmp_path):
        """Test read_bulk with size larger than file"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test\n2,test2\n")

        with open_iterable(test_file) as source:
            chunk = source.read_bulk(num=1000000)
            # Should return all available rows
            assert len(chunk) == 2

    def test_write_bulk_empty_list(self, tmp_path):
        """Test write_bulk with empty list"""
        output_file = tmp_path / "output.csv"

        with open_iterable(output_file, "w") as dest:
            dest.write_bulk([])

        # File should exist but may be empty or have header only
        assert output_file.exists()

    def test_write_bulk_none(self, tmp_path):
        """Test write_bulk with None"""
        output_file = tmp_path / "output.csv"

        with open_iterable(output_file, "w") as dest:
            with pytest.raises((TypeError, ValueError)):
                dest.write_bulk(None)  # type: ignore


class TestResetEdgeCases:
    """Test edge cases in reset operations"""

    def test_reset_before_read(self, tmp_path):
        """Test reset before any read"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test\n")

        with open_iterable(test_file) as source:
            # Reset should work even before reading
            source.reset()
            row = source.read()
            assert row["id"] == "1"

    def test_reset_after_close(self, tmp_path):
        """Test reset after close should fail"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test\n")

        source = open_iterable(test_file)
        source.close()

        with pytest.raises((ValueError, OSError, AttributeError)):
            source.reset()


class TestContextManagerEdgeCases:
    """Test edge cases with context managers"""

    def test_nested_context_managers(self, tmp_path):
        """Test nested context managers"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test\n2,test2\n")

        with open_iterable(test_file) as source1:
            rows1 = []
            for i, row in enumerate(source1):
                rows1.append(row)
                if i >= 0:
                    break

            with open_iterable(test_file) as source2:
                rows2 = []
                for i, row in enumerate(source2):
                    rows2.append(row)
                    if i >= 0:
                        break

            # Both should work independently
            assert rows1[0] == rows2[0]

    def test_context_manager_exception(self, tmp_path):
        """Test context manager cleanup on exception"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test\n")

        try:
            with open_iterable(test_file) as source:
                row = source.read()
                assert row is not None
                raise ValueError("Test exception")
        except ValueError:
            pass

        # File should be properly closed even after exception
        # Try to open again to verify
        with open_iterable(test_file) as source:
            row = source.read()
            assert row is not None


class TestFormatDetectionEdgeCases:
    """Test edge cases in format detection"""

    def test_detect_no_extension(self, tmp_path):
        """Test format detection for file without extension"""
        test_file = tmp_path / "test"
        test_file.write_text("id,name\n1,test\n")

        # Should detect from content
        with open_iterable(test_file) as source:
            row = source.read()
            assert row is not None

    def test_detect_unknown_extension(self, tmp_path):
        """Test format detection for unknown extension"""
        test_file = tmp_path / "test.unknown"
        test_file.write_text("id,name\n1,test\n")

        # Should try to detect from content
        try:
            with open_iterable(test_file) as source:
                row = source.read()
                assert row is not None
        except FormatDetectionError:
            # If detection fails, that's also acceptable
            pass

    def test_detect_empty_filename(self):
        """Test format detection with empty filename"""
        with pytest.raises((ValueError, FormatDetectionError)):
            open_iterable("")


class TestWriteNotSupportedEdgeCases:
    """Test edge cases for write-not-supported formats"""

    def test_write_to_read_only_format(self, tmp_path):
        """Test writing to format that doesn't support write"""
        # Use a format that doesn't support writing (e.g., ARFF)
        try:
            from iterable.datatypes.arff import ARFFIterable

            output_file = tmp_path / "output.arff"
            with pytest.raises(WriteNotSupportedError):
                with ARFFIterable(filename=str(output_file), mode="w") as dest:
                    dest.write({"id": 1})
        except ImportError:
            pytest.skip("ARFF format not available")


class TestEncodingEdgeCases:
    """Test edge cases with different encodings"""

    def test_invalid_encoding(self, tmp_path):
        """Test with invalid encoding name"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test\n")

        # Should either work with fallback or raise clear error
        try:
            with open_iterable(test_file, iterableargs={"encoding": "invalid_encoding_xyz"}) as source:
                row = source.read()
                assert row is not None
        except (LookupError, ValueError) as e:
            # Raising error for invalid encoding is acceptable
            assert "encoding" in str(e).lower() or "codec" in str(e).lower()

    def test_binary_mode_text_file(self, tmp_path):
        """Test opening text file in binary mode"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test\n")

        # Binary mode should still work for CSV (it handles encoding)
        with open_iterable(test_file, mode="rb") as source:
            row = source.read()
            assert row is not None


class TestOptionsEdgeCases:
    """Test edge cases with options dictionary"""

    def test_options_none(self, tmp_path):
        """Test with options=None"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test\n")

        # Should work with options=None
        with open_iterable(test_file, iterableargs=None) as source:  # type: ignore
            row = source.read()
            assert row is not None

    def test_options_empty_dict(self, tmp_path):
        """Test with options={}"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test\n")

        with open_iterable(test_file, iterableargs={}) as source:
            row = source.read()
            assert row is not None

    def test_options_invalid_key(self, tmp_path):
        """Test with invalid option keys"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test\n")

        # Invalid keys should either be ignored or raise error
        # Most implementations will just set the attribute
        with open_iterable(test_file, iterableargs={"invalid_key_xyz": "value"}) as source:
            row = source.read()
            assert row is not None
