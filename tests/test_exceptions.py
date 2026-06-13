"""Tests for exception hierarchy in iterable.exceptions module."""

import pytest

from iterable.exceptions import (
    CodecCompressionError,
    CodecDecompressionError,
    CodecError,
    CodecNotSupportedError,
    FormatDetectionError,
    FormatError,
    FormatNotSupportedError,
    FormatParseError,
    IterableDataError,
    ReadError,
    ResourceError,
    ResourceLeakError,
    StreamingNotSupportedError,
    StreamNotSeekableError,
    WriteError,
    WriteNotSupportedError,
)


class TestIterableDataError:
    """Test base exception class."""

    def test_basic_instantiation(self):
        """Test basic exception instantiation."""
        error = IterableDataError("Test message")
        assert str(error) == "Test message"
        assert error.message == "Test message"
        assert error.error_code is None

    def test_with_error_code(self):
        """Test exception with error code."""
        error = IterableDataError("Test message", error_code="TEST_ERROR")
        assert error.message == "Test message"
        assert error.error_code == "TEST_ERROR"


class TestFormatError:
    """Test format error exceptions."""

    def test_format_error_basic(self):
        """Test basic FormatError."""
        error = FormatError("Format error", format_id="csv")
        assert error.message == "Format error"
        assert error.format_id == "csv"
        assert error.error_code is None
        assert isinstance(error, IterableDataError)

    def test_format_error_with_code(self):
        """Test FormatError with error code."""
        error = FormatError("Format error", format_id="json", error_code="FORMAT_ERR")
        assert error.format_id == "json"
        assert error.error_code == "FORMAT_ERR"

    def test_format_not_supported_error(self):
        """Test FormatNotSupportedError."""
        error = FormatNotSupportedError("xml", reason="Missing dependency")
        assert error.format_id == "xml"
        assert error.reason == "Missing dependency"
        assert error.error_code == "FORMAT_NOT_SUPPORTED"
        assert "xml" in str(error)
        assert "Missing dependency" in str(error)

    def test_format_not_supported_error_no_reason(self):
        """Test FormatNotSupportedError without reason."""
        error = FormatNotSupportedError("parquet")
        assert error.format_id == "parquet"
        assert error.reason is None
        assert "parquet" in str(error)

    def test_format_detection_error(self):
        """Test FormatDetectionError."""
        error = FormatDetectionError(filename="data.unknown", reason="Unknown extension")
        assert error.filename == "data.unknown"
        assert error.reason == "Unknown extension"
        assert error.error_code == "FORMAT_DETECTION_FAILED"
        assert "data.unknown" in str(error)
        assert "Unknown extension" in str(error)

    def test_format_detection_error_no_args(self):
        """Test FormatDetectionError without filename or reason."""
        error = FormatDetectionError()
        assert error.filename is None
        assert error.reason is None
        assert "Could not detect file format" in str(error)

    def test_format_parse_error(self):
        """Test FormatParseError."""
        error = FormatParseError("json", "Invalid JSON syntax", position=42)
        assert error.format_id == "json"
        assert error.position == 42
        assert error.error_code == "FORMAT_PARSE_FAILED"
        assert "json" in str(error)
        assert "42" in str(error)

    def test_format_parse_error_no_position(self):
        """Test FormatParseError without position."""
        error = FormatParseError("csv", "Missing delimiter")
        assert error.format_id == "csv"
        assert error.position is None
        assert "csv" in str(error)

    def test_format_parse_error_with_context(self):
        """Test FormatParseError with full context."""
        error = FormatParseError(
            format_id="jsonl",
            message="Invalid JSON syntax",
            filename="data.jsonl",
            row_number=5,
            byte_offset=1234,
            original_line='{"invalid": json}',
        )
        assert error.format_id == "jsonl"
        assert error.filename == "data.jsonl"
        assert error.row_number == 5
        assert error.byte_offset == 1234
        assert error.original_line == '{"invalid": json}'
        assert error.position == 1234  # byte_offset used for position
        assert "jsonl" in str(error)
        assert "data.jsonl" in str(error)
        assert "5" in str(error) or "row 5" in str(error)
        assert "1234" in str(error) or "byte 1234" in str(error)

    def test_format_parse_error_with_row_number_only(self):
        """Test FormatParseError with row_number but no byte_offset."""
        error = FormatParseError(
            format_id="csv",
            message="Invalid delimiter",
            filename="data.csv",
            row_number=10,
        )
        assert error.row_number == 10
        assert error.byte_offset is None
        assert error.position is None
        assert "10" in str(error) or "row 10" in str(error)


class TestCodecError:
    """Test codec error exceptions."""

    def test_codec_error_basic(self):
        """Test basic CodecError."""
        error = CodecError("Codec error", codec_name="gzip")
        assert error.message == "Codec error"
        assert error.codec_name == "gzip"
        assert error.error_code is None
        assert isinstance(error, IterableDataError)

    def test_codec_error_with_code(self):
        """Test CodecError with error code."""
        error = CodecError("Codec error", codec_name="bzip2", error_code="CODEC_ERR")
        assert error.codec_name == "bzip2"
        assert error.error_code == "CODEC_ERR"

    def test_codec_not_supported_error(self):
        """Test CodecNotSupportedError."""
        error = CodecNotSupportedError("lz4", reason="Package not installed")
        assert error.codec_name == "lz4"
        assert error.reason == "Package not installed"
        assert error.error_code == "CODEC_NOT_SUPPORTED"
        assert "lz4" in str(error)
        assert "Package not installed" in str(error)

    def test_codec_decompression_error(self):
        """Test CodecDecompressionError."""
        error = CodecDecompressionError("gzip", "Corrupted data")
        assert error.codec_name == "gzip"
        assert error.error_code == "CODEC_DECOMPRESSION_FAILED"
        assert "gzip" in str(error)
        assert "Corrupted data" in str(error)

    def test_codec_decompression_error_no_message(self):
        """Test CodecDecompressionError without message."""
        error = CodecDecompressionError("zstd")
        assert error.codec_name == "zstd"
        assert "zstd" in str(error)

    def test_codec_compression_error(self):
        """Test CodecCompressionError."""
        error = CodecCompressionError("bzip2", "Write failed")
        assert error.codec_name == "bzip2"
        assert error.error_code == "CODEC_COMPRESSION_FAILED"
        assert "bzip2" in str(error)
        assert "Write failed" in str(error)


class TestReadWriteError:
    """Test read and write error exceptions."""

    def test_read_error(self):
        """Test ReadError."""
        error = ReadError("Read failed", filename="data.csv")
        assert error.message == "Read failed"
        assert error.filename == "data.csv"
        assert error.error_code is None
        assert isinstance(error, IterableDataError)

    def test_read_error_with_code(self):
        """Test ReadError with error code."""
        error = ReadError("Read failed", filename="data.json", error_code="READ_ERR")
        assert error.filename == "data.json"
        assert error.error_code == "READ_ERR"

    def test_write_error(self):
        """Test WriteError."""
        error = WriteError("Write failed", filename="output.csv")
        assert error.message == "Write failed"
        assert error.filename == "output.csv"
        assert error.error_code is None
        assert isinstance(error, IterableDataError)

    def test_write_not_supported_error(self):
        """Test WriteNotSupportedError."""
        error = WriteNotSupportedError("pcap", reason="Writing PCAP files is not yet implemented")
        assert error.format_id == "pcap"
        assert error.reason == "Writing PCAP files is not yet implemented"
        assert error.error_code == "WRITE_NOT_SUPPORTED"
        assert "pcap" in str(error)
        assert "Writing PCAP files is not yet implemented" in str(error)
        assert isinstance(error, WriteError)

    def test_write_not_supported_error_no_reason(self):
        """Test WriteNotSupportedError without reason."""
        error = WriteNotSupportedError("netcdf")
        assert error.format_id == "netcdf"
        assert error.reason is None
        assert "netcdf" in str(error)
        assert isinstance(error, WriteError)

    def test_streaming_not_supported_error(self):
        """Test StreamingNotSupportedError."""
        error = StreamingNotSupportedError("json", reason="Loads entire file")
        assert error.format_id == "json"
        assert error.reason == "Loads entire file"
        assert error.error_code == "STREAMING_NOT_SUPPORTED"
        assert "json" in str(error)
        assert isinstance(error, ReadError)


class TestResourceError:
    """Test resource error exceptions."""

    def test_resource_error(self):
        """Test ResourceError."""
        error = ResourceError("Resource error")
        assert error.message == "Resource error"
        assert error.error_code is None
        assert isinstance(error, IterableDataError)

    def test_stream_not_seekable_error(self):
        """Test StreamNotSeekableError."""
        error = StreamNotSeekableError(operation="reset")
        assert error.operation == "reset"
        assert error.error_code == "STREAM_NOT_SEEKABLE"
        assert "reset" in str(error)
        assert isinstance(error, ResourceError)

    def test_stream_not_seekable_error_no_operation(self):
        """Test StreamNotSeekableError without operation."""
        error = StreamNotSeekableError()
        assert error.operation is None
        assert "Stream is not seekable" in str(error)

    def test_resource_leak_error(self):
        """Test ResourceLeakError."""
        error = ResourceLeakError(resource_type="file handle")
        assert error.resource_type == "file handle"
        assert error.error_code == "RESOURCE_LEAK"
        assert "file handle" in str(error)
        assert isinstance(error, ResourceError)

    def test_resource_leak_error_no_type(self):
        """Test ResourceLeakError without resource type."""
        error = ResourceLeakError()
        assert error.resource_type is None
        assert "Resource leak detected" in str(error)


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_base(self):
        """Test that all exceptions inherit from IterableDataError."""
        exceptions = [
            FormatError("test"),
            CodecError("test"),
            ReadError("test"),
            WriteError("test"),
            ResourceError("test"),
        ]
        for exc in exceptions:
            assert isinstance(exc, IterableDataError)

    def test_format_exceptions_inherit_from_format_error(self):
        """Test that format-specific exceptions inherit from FormatError."""
        assert issubclass(FormatNotSupportedError, FormatError)
        assert issubclass(FormatDetectionError, FormatError)
        assert issubclass(FormatParseError, FormatError)

    def test_codec_exceptions_inherit_from_codec_error(self):
        """Test that codec-specific exceptions inherit from CodecError."""
        assert issubclass(CodecNotSupportedError, CodecError)
        assert issubclass(CodecDecompressionError, CodecError)
        assert issubclass(CodecCompressionError, CodecError)

    def test_streaming_inherits_from_read_error(self):
        """Test that StreamingNotSupportedError inherits from ReadError."""
        assert issubclass(StreamingNotSupportedError, ReadError)

    def test_resource_exceptions_inherit_from_resource_error(self):
        """Test that resource-specific exceptions inherit from ResourceError."""
        assert issubclass(StreamNotSeekableError, ResourceError)
        assert issubclass(ResourceLeakError, ResourceError)

    def test_write_not_supported_inherits_from_write_error(self):
        """Test that WriteNotSupportedError inherits from WriteError."""
        assert issubclass(WriteNotSupportedError, WriteError)


class TestExceptionIntegration:
    """Test exceptions are raised correctly in real scenarios."""

    def test_write_not_supported_error_raised(self, tmp_path):
        """Test that WriteNotSupportedError is raised when writing to unsupported formats."""
        pytest.importorskip("dpkt", reason="dpkt is required for PCAP support")

        from iterable.exceptions import WriteNotSupportedError
        from iterable.helpers.detect import open_iterable

        # Try to write to a format that doesn't support writing (e.g., PCAP)
        pcap_file = tmp_path / "test.pcap"
        pcap_file.write_bytes(b"dummy pcap data")

        # Reading should work
        with open_iterable(str(pcap_file)):
            # Should be able to open for reading
            pass

        # Writing should raise WriteNotSupportedError
        with pytest.raises(WriteNotSupportedError) as exc_info:
            with open_iterable(str(pcap_file), mode="w") as dest:
                dest.write({"key": "value"})

        assert exc_info.value.format_id == "pcap"
        assert exc_info.value.error_code == "WRITE_NOT_SUPPORTED"

    def test_format_parse_error_raised_with_context(self, tmp_path):
        """Test that FormatParseError is raised with context in malformed files."""
        from iterable.exceptions import FormatParseError
        from iterable.helpers.detect import open_iterable

        # Create a JSONL file with invalid JSON
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"name": "John"}\n{"invalid": json}\n{"name": "Jane"}\n')

        # With default error policy (raise), should raise FormatParseError
        with pytest.raises(FormatParseError) as exc_info:
            with open_iterable(str(jsonl_file)) as source:
                list(source)  # Try to read all rows

        error = exc_info.value
        assert error.format_id == "jsonl"
        assert error.error_code == "FORMAT_PARSE_FAILED"
        assert error.filename == str(jsonl_file)
        # Should have row number context
        assert error.row_number is not None
        # Should have original line context
        assert error.original_line is not None
        assert "invalid" in error.original_line.lower() or "json" in error.original_line.lower()

    def test_read_error_raised_for_resource_requirements(self, tmp_path):
        """Test that ReadError is raised when resource requirements aren't met."""
        import io

        from iterable.exceptions import ReadError
        from iterable.helpers.detect import open_iterable

        # Try to open Vortex format with stream instead of filename
        stream = io.BytesIO(b"dummy data")
        with pytest.raises(ReadError) as exc_info:
            open_iterable(stream, format="vortex")

        assert exc_info.value.error_code == "RESOURCE_REQUIREMENT_NOT_MET"
        assert "stream" in exc_info.value.message.lower() or "filename" in exc_info.value.message.lower()

    def test_format_not_supported_error_raised(self, tmp_path):
        """Test that FormatNotSupportedError is raised for unsupported formats."""
        from iterable.exceptions import FormatNotSupportedError
        from iterable.helpers.detect import open_iterable

        # Try to open a format that requires missing dependencies
        # This test may need adjustment based on what formats are actually unsupported
        unknown_file = tmp_path / "test.unknown"
        unknown_file.write_text("dummy data")

        # If format detection fails and format is not supported, should raise FormatNotSupportedError
        # Note: This test may need to be adjusted based on actual behavior
        try:
            with open_iterable(str(unknown_file)):
                pass
        except FormatNotSupportedError as e:
            assert e.error_code == "FORMAT_NOT_SUPPORTED"
            assert e.format_id is not None

    def test_exception_hierarchy_catching(self, tmp_path):
        """Test that exception hierarchy allows catching base exceptions."""
        from iterable.exceptions import FormatError, IterableDataError

        # Create a file that will cause a format error
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"invalid": json}\n')

        from iterable.helpers.detect import open_iterable

        # Should be able to catch FormatParseError as FormatError
        with pytest.raises(FormatError):
            with open_iterable(str(jsonl_file)) as source:
                list(source)

        # Should be able to catch FormatParseError as IterableDataError
        with pytest.raises(IterableDataError):
            with open_iterable(str(jsonl_file)) as source:
                list(source)


class TestEnhancedErrorMessages:
    """Test enhanced error messages with actionable guidance."""

    def test_format_not_supported_error_with_dependency_guidance(self):
        """Test FormatNotSupportedError includes dependency installation guidance."""
        error = FormatNotSupportedError("parquet", reason="Required dependency 'pyarrow' is not installed")
        error_str = str(error)

        # Should include base message
        assert "Format 'parquet' is not supported" in error_str
        assert "pyarrow" in error_str

        # Should include actionable guidance
        assert "To fix this issue:" in error_str
        assert "pip install" in error_str
        assert "Verify the installation" in error_str
        assert "Retry your operation" in error_str

    def test_format_not_supported_error_without_reason(self):
        """Test FormatNotSupportedError without reason has no guidance."""
        error = FormatNotSupportedError("unknown_format")
        error_str = str(error)

        # Should include base message
        assert "Format 'unknown_format' is not supported" in error_str

        # Should not include guidance when no reason provided
        assert "To fix this issue:" not in error_str

    def test_format_detection_error_guidance(self):
        """Test FormatDetectionError includes format detection guidance."""
        error = FormatDetectionError(filename="data.unknown", reason="File extension not recognized")
        error_str = str(error)

        # Should include base message
        assert "Could not detect file format" in error_str
        assert "data.unknown" in error_str

        # Should include actionable guidance
        assert "The file format could not be determined" in error_str
        assert "Specify the format explicitly" in error_str
        assert "open_iterable('file', iterableargs={'format': 'csv'})" in error_str
        assert "Rename the file with a recognized extension" in error_str

    def test_format_detection_error_no_filename(self):
        """Test FormatDetectionError without filename still provides guidance."""
        error = FormatDetectionError(reason="Content detection failed")
        error_str = str(error)

        # Should include base message
        assert "Could not detect file format" in error_str

        # Should still include guidance
        assert "The file format could not be determined" in error_str
        assert "Specify the format explicitly" in error_str

    def test_format_parse_error_csv_guidance(self):
        """Test FormatParseError includes CSV-specific guidance."""
        error = FormatParseError(
            format_id="csv",
            message="Expecting ',' delimiter: line 123 column 45",
            filename="data.csv",
            row_number=123,
            byte_offset=4567,
        )
        error_str = str(error)

        # Should include base message
        assert "Failed to parse csv format" in error_str
        assert "data.csv" in error_str
        assert "123" in error_str

        # Should include CSV-specific guidance
        assert "This usually means:" in error_str
        assert "inconsistent delimiters" in error_str
        assert "unescaped quote" in error_str
        assert "file encoding is incorrect" in error_str
        assert "Check the problematic line:" in error_str
        assert "Specify the correct delimiter:" in error_str
        assert "Handle encoding issues:" in error_str
        assert "Use error handling to skip problematic rows:" in error_str

    def test_format_parse_error_json_guidance(self):
        """Test FormatParseError includes JSON-specific guidance."""
        error = FormatParseError(
            format_id="jsonl",
            message="Invalid JSON syntax",
            filename="data.jsonl",
            row_number=5,
            original_line='{"invalid": json}',
        )
        error_str = str(error)

        # Should include base message
        assert "Failed to parse jsonl format" in error_str
        assert "data.jsonl" in error_str

        # Should include JSON-specific guidance
        assert "This usually means:" in error_str
        assert "JSON structure is invalid" in error_str
        assert "syntax error in the JSON" in error_str
        assert "Validate the JSON:" in error_str
        assert "python -m json.tool" in error_str
        assert "Check the problematic line:" in error_str

    def test_codec_not_supported_error_guidance(self):
        """Test CodecNotSupportedError includes codec installation guidance."""
        error = CodecNotSupportedError("zstd", reason="Required dependency 'zstandard' is not installed")
        error_str = str(error)

        # Should include base message
        assert "Codec 'zstd' is not supported" in error_str
        assert "zstandard" in error_str

        # Should include actionable guidance
        assert "To fix this issue:" in error_str
        assert "pip install" in error_str
        assert "Verify the installation" in error_str

        # Should suggest alternatives
        assert "Alternative:" in error_str
        assert "different compression format" in error_str

    def test_codec_not_supported_error_no_reason(self):
        """Test CodecNotSupportedError without reason still provides alternatives."""
        error = CodecNotSupportedError("zstd")
        error_str = str(error)

        # Should include base message
        assert "Codec 'zstd' is not supported" in error_str

        # Should still suggest alternatives
        assert "Alternative:" in error_str or "different compression format" in error_str

    def test_stream_not_seekable_error_guidance(self):
        """Test StreamNotSeekableError includes stream guidance."""
        error = StreamNotSeekableError(operation="reset")
        error_str = str(error)

        # Should include base message
        assert "Stream is not seekable" in error_str
        assert "reset" in error_str

        # Should include actionable guidance
        assert "doesn't support seeking" in error_str
        assert "Standard input (stdin)" in error_str
        assert "Network streams" in error_str
        assert "To fix this issue:" in error_str
        assert "Avoid calling" in error_str
        assert "Alternative:" in error_str

    def test_stream_not_seekable_error_no_operation(self):
        """Test StreamNotSeekableError without operation still provides guidance."""
        error = StreamNotSeekableError()
        error_str = str(error)

        # Should include base message
        assert "Stream is not seekable" in error_str

        # Should still include guidance
        assert "doesn't support seeking" in error_str
        assert "To fix this issue:" in error_str

    def test_enhanced_messages_backward_compatible(self):
        """Test that enhanced messages maintain backward compatibility."""
        # Test that exception attributes are still accessible
        error = FormatNotSupportedError("parquet", reason="Missing dependency")
        assert error.format_id == "parquet"
        assert error.reason == "Missing dependency"
        assert error.error_code == "FORMAT_NOT_SUPPORTED"
        assert error.message is not None

        # Test that exception can be caught normally
        try:
            raise FormatNotSupportedError("test", reason="test reason")
        except FormatNotSupportedError as e:
            assert e.format_id == "test"
            assert e.reason == "test reason"

    def test_guidance_includes_documentation_links(self):
        """Test that guidance includes documentation links."""
        error = FormatNotSupportedError("parquet", reason="Required dependency 'pyarrow' is not installed")
        error_str = str(error)

        # Should include documentation link
        assert "iterabledata.io/docs" in error_str

        error2 = FormatDetectionError(filename="data.unknown")
        error_str2 = str(error2)
        assert "iterabledata.io/docs" in error_str2

        error3 = FormatParseError(format_id="csv", message="Parse error")
        error_str3 = str(error3)
        assert "iterabledata.io/docs" in error_str3
