"""Tests for structured logging framework."""

import json
import logging
import os
from io import StringIO

from iterable.helpers.structured_logging import (
    HumanReadableFormatter,
    LogEventType,
    OperationContext,
    StructuredJSONFormatter,
    configure_structured_logging,
    is_structured_logging_enabled,
)


class TestStructuredLoggingInfrastructure:
    """Tests for structured logging infrastructure."""

    def test_json_formatter_basic(self):
        """Test JSON formatter creates valid JSON."""
        formatter = StructuredJSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test"
        assert log_data["message"] == "Test message"
        assert "timestamp" in log_data

    def test_json_formatter_with_context(self):
        """Test JSON formatter includes structured context."""
        formatter = StructuredJSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        # Add structured context
        record.event_type = LogEventType.FORMAT_DETECTION
        record.filename = "test.csv"
        record.format_id = "csv"
        record.confidence = 1.0

        output = formatter.format(record)
        log_data = json.loads(output)

        assert log_data["event_type"] == LogEventType.FORMAT_DETECTION
        # Check that structured context fields are included
        assert "filename" in log_data or "format_id" in log_data  # At least one context field
        assert log_data.get("format_id") == "csv"
        assert log_data.get("confidence") == 1.0
        # filename should be included if it's JSON-serializable
        if "filename" in log_data:
            assert log_data["filename"] == "test.csv"

    def test_human_readable_formatter(self):
        """Test human-readable formatter creates readable output."""
        formatter = HumanReadableFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.event_type = LogEventType.FILE_IO
        record.operation = "open"

        output = formatter.format(record)

        assert "[INFO]" in output
        assert "test" in output
        assert "Test message" in output
        assert "event_type=file_io" in output or "event_type=FILE_IO" in output

    def test_operation_context(self):
        """Test OperationContext generates operation IDs."""
        with OperationContext("test_operation", key="value") as ctx:
            assert ctx.operation_id is not None
            assert len(ctx.operation_id) > 0
            assert ctx.operation_type == "test_operation"
            assert ctx.context == {"key": "value"}

    def test_operation_context_propagation(self):
        """Test OperationContext propagates operation ID to logs."""
        from iterable.helpers.structured_logging import operation_id

        formatter = StructuredJSONFormatter()

        with OperationContext("test_operation"):
            op_id = operation_id.get()
            assert op_id is not None

            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test message",
                args=(),
                exc_info=None,
            )

            output = formatter.format(record)
            log_data = json.loads(output)

            assert log_data["operation_id"] == op_id

    def test_configure_structured_logging_json(self):
        """Test configuring structured logging with JSON format."""
        logger = logging.getLogger("iterable.test")
        handler = logging.StreamHandler(StringIO())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        configure_structured_logging(format="json", level=logging.INFO, handler=handler)

        logger.info("Test message", extra={"event_type": LogEventType.FORMAT_DETECTION})

        # Verify handler has JSON formatter
        assert isinstance(handler.formatter, StructuredJSONFormatter)

    def test_configure_structured_logging_human(self):
        """Test configuring structured logging with human-readable format."""
        logger = logging.getLogger("iterable.test")
        handler = logging.StreamHandler(StringIO())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        configure_structured_logging(format="human", level=logging.INFO, handler=handler)

        logger.info("Test message", extra={"event_type": LogEventType.FILE_IO})

        # Verify handler has human-readable formatter
        assert isinstance(handler.formatter, HumanReadableFormatter)

    def test_is_structured_logging_enabled(self):
        """Test checking if structured logging is enabled."""
        # Save original value
        original = os.environ.get("ITERABLEDATA_STRUCTURED_LOGGING")

        try:
            # Test disabled
            os.environ.pop("ITERABLEDATA_STRUCTURED_LOGGING", None)
            assert not is_structured_logging_enabled()

            # Test enabled
            os.environ["ITERABLEDATA_STRUCTURED_LOGGING"] = "1"
            assert is_structured_logging_enabled()

            os.environ["ITERABLEDATA_STRUCTURED_LOGGING"] = "true"
            assert is_structured_logging_enabled()
        finally:
            # Restore original value
            if original is not None:
                os.environ["ITERABLEDATA_STRUCTURED_LOGGING"] = original
            else:
                os.environ.pop("ITERABLEDATA_STRUCTURED_LOGGING", None)

    def test_log_event_types(self):
        """Test LogEventType constants."""
        assert LogEventType.FORMAT_DETECTION == "format_detection"
        assert LogEventType.FILE_IO == "file_io"
        assert LogEventType.PARSING == "parsing"
        assert LogEventType.CONVERSION == "conversion"
        assert LogEventType.PIPELINE == "pipeline"
        assert LogEventType.ERROR == "error"
        assert LogEventType.PERFORMANCE == "performance"
        assert LogEventType.VALIDATION == "validation"

    def test_json_formatter_with_exception(self):
        """Test JSON formatter includes exception information."""
        formatter = StructuredJSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Test error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )

            output = formatter.format(record)
            log_data = json.loads(output)

            assert log_data["level"] == "ERROR"
            assert "exception" in log_data
            assert "ValueError" in log_data["exception"]
            assert "Test error" in log_data["exception"]
