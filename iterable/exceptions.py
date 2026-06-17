"""Exception hierarchy for IterableData library.

This module defines a comprehensive exception hierarchy that allows users
to catch and handle specific error types programmatically.
"""

from .guidance import ErrorGuidance


class IterableDataError(Exception):
    """Base exception for all iterable data errors.

    All exceptions raised by the IterableData library inherit from this class,
    allowing users to catch all iterable errors with a single exception handler.
    """

    def __init__(self, message: str, error_code: str | None = None):
        """Initialize exception.

        Args:
            message: Human-readable error message
            error_code: Optional error code for programmatic handling
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class FormatError(IterableDataError):
    """Base exception for format-specific errors.

    Raised when an error occurs related to data format handling.
    """

    def __init__(self, message: str, format_id: str | None = None, error_code: str | None = None):
        """Initialize format error.

        Args:
            message: Human-readable error message
            format_id: Optional format identifier (e.g., "csv", "json")
            error_code: Optional error code for programmatic handling
        """
        super().__init__(message, error_code)
        self.format_id = format_id


class FormatNotSupportedError(FormatError, ValueError, RuntimeError):
    """Format is not supported or not available.

    Raised when a requested format is not supported by the library,
    or when required dependencies are missing. Also a ``ValueError`` subclass
    so that callers following the documented ``open_iterable`` contract can
    catch it as an invalid-argument error, and a ``RuntimeError`` subclass so
    that ``open_iterable``'s documented "format could not be detected" failures
    can be caught as ``RuntimeError`` as well.

    Error code: FORMAT_NOT_SUPPORTED
    """

    def __init__(self, format_id: str, reason: str | None = None):
        """Initialize format not supported error.

        Args:
            format_id: Format identifier that is not supported
            reason: Optional reason why format is not supported
        """
        message = f"Format '{format_id}' is not supported"
        if reason:
            message += f": {reason}"
        super().__init__(message, format_id=format_id, error_code="FORMAT_NOT_SUPPORTED")
        self.reason = reason

    def __str__(self) -> str:
        """Return enhanced error message with actionable guidance."""
        base_message = super().__str__()
        guidance = ErrorGuidance.format_not_supported(self.format_id, self.reason) if self.format_id else ""

        if guidance:
            return f"{base_message}\n\n{guidance}"
        return base_message


class FormatDetectionError(FormatError):
    """Could not detect file format.

    Raised when the system cannot determine the format of a file,
    either from filename extension or content analysis.

    Error code: FORMAT_DETECTION_FAILED
    """

    def __init__(self, filename: str | None = None, reason: str | None = None):
        """Initialize format detection error.

        Args:
            filename: Optional filename that could not be detected
            reason: Optional reason why detection failed
        """
        message = "Could not detect file format"
        if filename:
            message += f" for file: {filename}"
        if reason:
            message += f". {reason}"
        super().__init__(message, error_code="FORMAT_DETECTION_FAILED")
        self.filename = filename
        self.reason = reason

    def __str__(self) -> str:
        """Return enhanced error message with actionable guidance."""
        base_message = super().__str__()
        guidance = ErrorGuidance.format_detection_failed(self.filename, self.reason)

        if guidance:
            return f"{base_message}\n\n{guidance}"
        return base_message


class FormatParseError(FormatError, ValueError):
    """Format parsing failed.

    Raised when a file cannot be parsed as the expected format,
    typically due to malformed data. Also a ``ValueError`` subclass since a
    parse failure is fundamentally an invalid-value condition, so callers can
    catch it with ``except ValueError``.

    Error code: FORMAT_PARSE_FAILED
    """

    def __init__(
        self,
        format_id: str,
        message: str,
        position: int | None = None,
        filename: str | None = None,
        row_number: int | None = None,
        byte_offset: int | None = None,
        original_line: str | None = None,
    ):
        """Initialize format parse error.

        Args:
            format_id: Format identifier
            message: Error message describing the parse failure
            position: Optional position in file where error occurred (deprecated, use byte_offset)
            filename: Optional filename where error occurred
            row_number: Optional row number (1-indexed, header excluded)
            byte_offset: Optional byte offset in file where error occurred
            original_line: Optional original line content that failed to parse (for text formats)
        """
        # Build error message with available context
        full_message = f"Failed to parse {format_id} format"

        # Use byte_offset if available, otherwise fall back to position for backward compatibility
        offset = byte_offset if byte_offset is not None else position

        if filename:
            full_message += f" at {filename}"
        if row_number is not None:
            full_message += f":{row_number}"
        if offset is not None:
            full_message += f" (byte {offset})"
        full_message += f": {message}"

        super().__init__(full_message, format_id=format_id, error_code="FORMAT_PARSE_FAILED")
        # Keep `position` for backward compatibility; fall back to byte_offset
        # when position is not explicitly provided.
        self.position = position if position is not None else byte_offset
        self.filename = filename
        self.row_number = row_number
        self.byte_offset = byte_offset
        self.original_line = original_line
        self.parse_message = message  # Store original parse error message for guidance

    def __str__(self) -> str:
        """Return enhanced error message with actionable guidance."""
        base_message = super().__str__()
        guidance = (
            ErrorGuidance.format_parse_error(
                self.format_id,
                self.parse_message,
                self.filename,
                self.row_number,
                self.byte_offset,
                self.original_line,
            )
            if self.format_id
            else ""
        )

        if guidance:
            return f"{base_message}\n\n{guidance}"
        return base_message


class CodecError(IterableDataError):
    """Base exception for compression codec errors.

    Raised when an error occurs related to compression/decompression.
    """

    def __init__(self, message: str, codec_name: str | None = None, error_code: str | None = None):
        """Initialize codec error.

        Args:
            message: Human-readable error message
            codec_name: Optional codec name (e.g., "gzip", "bzip2")
            error_code: Optional error code for programmatic handling
        """
        super().__init__(message, error_code)
        self.codec_name = codec_name


class CodecNotSupportedError(CodecError):
    """Compression codec is not supported.

    Raised when a requested codec is not available,
    typically due to missing dependencies.

    Error code: CODEC_NOT_SUPPORTED
    """

    def __init__(self, codec_name: str, reason: str | None = None):
        """Initialize codec not supported error.

        Args:
            codec_name: Codec name that is not supported
            reason: Optional reason why codec is not supported
        """
        message = f"Codec '{codec_name}' is not supported"
        if reason:
            message += f": {reason}"
        super().__init__(message, codec_name=codec_name, error_code="CODEC_NOT_SUPPORTED")
        self.reason = reason

    def __str__(self) -> str:
        """Return enhanced error message with actionable guidance."""
        base_message = super().__str__()
        guidance = ErrorGuidance.codec_not_supported(self.codec_name, self.reason) if self.codec_name else ""

        if guidance:
            return f"{base_message}\n\n{guidance}"
        return base_message


class CodecDecompressionError(CodecError):
    """Decompression failed.

    Raised when decompressing data fails.

    Error code: CODEC_DECOMPRESSION_FAILED
    """

    def __init__(self, codec_name: str, message: str | None = None):
        """Initialize decompression error.

        Args:
            codec_name: Codec name
            message: Optional error message
        """
        error_message = f"Failed to decompress using {codec_name} codec"
        if message:
            error_message += f": {message}"
        super().__init__(error_message, codec_name=codec_name, error_code="CODEC_DECOMPRESSION_FAILED")


class CodecCompressionError(CodecError):
    """Compression failed.

    Raised when compressing data fails.

    Error code: CODEC_COMPRESSION_FAILED
    """

    def __init__(self, codec_name: str, message: str | None = None):
        """Initialize compression error.

        Args:
            codec_name: Codec name
            message: Optional error message
        """
        error_message = f"Failed to compress using {codec_name} codec"
        if message:
            error_message += f": {message}"
        super().__init__(error_message, codec_name=codec_name, error_code="CODEC_COMPRESSION_FAILED")


class ReadError(IterableDataError):
    """Base exception for reading errors.

    Raised when an error occurs during data reading operations.
    """

    def __init__(
        self,
        message: str,
        filename: str | None = None,
        error_code: str | None = None,
        row_number: int | None = None,
        byte_offset: int | None = None,
        original_line: str | None = None,
    ):
        """Initialize read error.

        Args:
            message: Human-readable error message
            filename: Optional filename being read
            error_code: Optional error code for programmatic handling
            row_number: Optional row number (1-indexed, header excluded)
            byte_offset: Optional byte offset in file where error occurred
            original_line: Optional original line content (for text formats)
        """
        super().__init__(message, error_code)
        self.filename = filename
        self.row_number = row_number
        self.byte_offset = byte_offset
        self.original_line = original_line


class WriteError(IterableDataError):
    """Base exception for writing errors.

    Raised when an error occurs during data writing operations.
    """

    def __init__(self, message: str, filename: str | None = None, error_code: str | None = None):
        """Initialize write error.

        Args:
            message: Human-readable error message
            filename: Optional filename being written
            error_code: Optional error code for programmatic handling
        """
        super().__init__(message, error_code)
        self.filename = filename


class WriteNotSupportedError(WriteError):
    """Write operation is not supported for this format.

    Raised when attempting to write to a format that doesn't support writing,
    or when write support hasn't been implemented yet.

    Error code: WRITE_NOT_SUPPORTED
    """

    def __init__(self, format_id: str, reason: str | None = None):
        """Initialize write not supported error.

        Args:
            format_id: Format identifier that doesn't support writing
            reason: Optional reason why writing is not supported
        """
        message = f"Writing to format '{format_id}' is not supported"
        if reason:
            message += f": {reason}"
        super().__init__(message, error_code="WRITE_NOT_SUPPORTED")
        self.format_id = format_id
        self.reason = reason


class StreamingNotSupportedError(ReadError):
    """Format doesn't support streaming.

    Raised when a streaming operation is attempted on a format
    that doesn't support streaming (e.g., formats that load entire file).

    Error code: STREAMING_NOT_SUPPORTED
    """

    def __init__(self, format_id: str, reason: str | None = None):
        """Initialize streaming not supported error.

        Args:
            format_id: Format identifier that doesn't support streaming
            reason: Optional reason why streaming is not supported
        """
        message = f"Format '{format_id}' does not support streaming"
        if reason:
            message += f": {reason}"
        super().__init__(message, error_code="STREAMING_NOT_SUPPORTED")
        self.format_id = format_id
        self.reason = reason


class ResourceError(IterableDataError):
    """Base exception for resource management errors.

    Raised when an error occurs related to resource management
    (file handles, streams, connections, etc.).
    """

    def __init__(self, message: str, error_code: str | None = None):
        """Initialize resource error.

        Args:
            message: Human-readable error message
            error_code: Optional error code for programmatic handling
        """
        super().__init__(message, error_code)


class StreamNotSeekableError(ResourceError):
    """Stream is not seekable.

    Raised when an operation requires seeking (e.g., reset())
    but the stream doesn't support seeking.

    Error code: STREAM_NOT_SEEKABLE
    """

    def __init__(self, operation: str | None = None):
        """Initialize stream not seekable error.

        Args:
            operation: Optional operation that requires seeking
        """
        message = "Stream is not seekable"
        if operation:
            message += f" (required for {operation})"
        super().__init__(message, error_code="STREAM_NOT_SEEKABLE")
        self.operation = operation

    def __str__(self) -> str:
        """Return enhanced error message with actionable guidance."""
        base_message = super().__str__()
        guidance = ErrorGuidance.stream_not_seekable(self.operation)

        if guidance:
            return f"{base_message}\n\n{guidance}"
        return base_message


class ResourceLeakError(ResourceError):
    """Resource leak detected.

    Raised when a resource (file, connection, etc.) is not properly closed.

    Error code: RESOURCE_LEAK
    """

    def __init__(self, resource_type: str | None = None):
        """Initialize resource leak error.

        Args:
            resource_type: Optional type of resource that leaked
        """
        message = "Resource leak detected"
        if resource_type:
            message += f": {resource_type}"
        super().__init__(message, error_code="RESOURCE_LEAK")
        self.resource_type = resource_type
