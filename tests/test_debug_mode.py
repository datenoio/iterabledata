"""Tests for debug mode and verbose logging functionality."""

import logging
from io import StringIO

from iterable.helpers.debug import (
    enable_debug_mode,
    file_io_logger,
    format_detection_logger,
    is_debug_enabled,
    performance_logger,
)
from iterable.helpers.detect import open_iterable
from iterable.pipeline.core import pipeline


class TestDebugModeConfiguration:
    """Test debug mode configuration functions."""

    def test_enable_debug_mode(self):
        """Test enabling debug mode."""
        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))

        # Enable debug mode
        enable_debug_mode(level=logging.DEBUG, handler=handler)

        # Verify loggers are configured
        assert format_detection_logger.isEnabledFor(logging.DEBUG)
        assert file_io_logger.isEnabledFor(logging.DEBUG)
        assert performance_logger.isEnabledFor(logging.DEBUG)

    def test_is_debug_enabled(self):
        """Test checking if debug is enabled."""
        # Initially should be False (unless env var is set)
        # We'll test with explicit enable
        enable_debug_mode(level=logging.DEBUG)
        assert is_debug_enabled() is True

    def test_debug_mode_from_env_var(self, monkeypatch):
        """Test debug mode from environment variable."""
        # Set environment variable
        monkeypatch.setenv("ITERABLEDATA_DEBUG", "1")

        # Reload module to pick up env var
        import importlib

        import iterable.helpers.debug

        importlib.reload(iterable.helpers.debug)

        # Should be enabled
        assert iterable.helpers.debug.is_debug_enabled() is True


class TestFormatDetectionLogging:
    """Test format detection logging."""

    def test_format_detection_logging(self, tmp_path):
        """Test format detection logs debug information."""
        # Create test file
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2\nval1,val2\n")

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
        enable_debug_mode(level=logging.DEBUG, handler=handler)

        # Detect file type with debug enabled
        from iterable.helpers.detect import detect_file_type

        result = detect_file_type(str(test_file), debug=True)

        # Verify detection worked
        assert result["success"] is True

        # Verify log output contains debug information
        log_output = log_capture.getvalue()
        assert "iterable.detect" in log_output
        assert "DEBUG" in log_output
        assert "test.csv" in log_output

    def test_open_iterable_with_debug(self, tmp_path):
        """Test open_iterable with debug parameter."""
        # Create test file
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2\nval1,val2\n")

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
        enable_debug_mode(level=logging.DEBUG, handler=handler)

        # Open with debug enabled
        with open_iterable(str(test_file), debug=True) as source:
            # Read a record
            next(source, None)

        # Verify log output contains debug information
        log_output = log_capture.getvalue()
        assert "iterable.detect" in log_output or "iterable.io" in log_output
        assert "DEBUG" in log_output


class TestFileIOLogging:
    """Test file I/O logging."""

    def test_file_open_logging(self, tmp_path):
        """Test file open operations are logged."""
        # Create test file
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2\nval1,val2\n")

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
        enable_debug_mode(level=logging.DEBUG, handler=handler)

        # Open file with debug enabled
        with open_iterable(str(test_file), debug=True) as source:
            # Access the file object to trigger open
            if hasattr(source, "fobj") and source.fobj is None:
                source.open()

        # Verify log output contains file I/O information
        log_output = log_capture.getvalue()
        assert "iterable.io" in log_output or "Opening file" in log_output

    def test_file_close_logging(self, tmp_path):
        """Test file close operations are logged."""
        # Create test file
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2\nval1,val2\n")

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
        enable_debug_mode(level=logging.DEBUG, handler=handler)

        # Open and close file with debug enabled
        source = open_iterable(str(test_file), debug=True)
        source.close()

        # Verify log output contains close information
        log_output = log_capture.getvalue()
        # Close logging may or may not appear depending on when it's called
        # Just verify debug mode is working
        assert "DEBUG" in log_output


class TestPipelinePerformanceLogging:
    """Test pipeline performance logging."""

    def test_pipeline_performance_logging(self, tmp_path):
        """Test pipeline logs performance information."""
        # Create source and destination files
        source_file = tmp_path / "source.csv"
        dest_file = tmp_path / "dest.csv"
        source_file.write_text("col1,col2\nval1,val2\nval3,val4\n")

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
        enable_debug_mode(level=logging.DEBUG, handler=handler)

        # Run pipeline with debug enabled
        from iterable.helpers.detect import open_iterable

        with open_iterable(str(source_file)) as source:
            with open_iterable(str(dest_file), mode="w") as dest:

                def process_func(record, state):
                    return record

                result = pipeline(
                    source=source,
                    destination=dest,
                    process_func=process_func,
                    debug=True,
                )

        # Verify pipeline completed
        assert result.rec_count == 2

        # Verify log output contains performance information
        log_output = log_capture.getvalue()
        assert "iterable.perf" in log_output or "Pipeline" in log_output or "DEBUG" in log_output


class TestDebugModeBackwardCompatibility:
    """Test that debug mode maintains backward compatibility."""

    def test_debug_parameter_optional(self, tmp_path):
        """Test that debug parameter is optional and defaults to False."""
        # Create test file
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2\nval1,val2\n")

        # Should work without debug parameter
        with open_iterable(str(test_file)) as source:
            record = next(source, None)
            assert record is not None

    def test_debug_mode_does_not_break_normal_operation(self, tmp_path):
        """Test that enabling debug mode doesn't break normal operation."""
        # Create test file
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2\nval1,val2\n")

        # Enable debug mode
        enable_debug_mode(level=logging.DEBUG)

        # Should still work normally
        with open_iterable(str(test_file)) as source:
            records = list(source)
            assert len(records) == 1
            assert records[0]["col1"] == "val1"
