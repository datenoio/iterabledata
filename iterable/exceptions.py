"""Exception hierarchy for IterableData library.

This module defines a comprehensive exception hierarchy that allows users
to catch and handle specific error types programmatically.
"""

import os
import re


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


# Helper functions for guidance generation


def _extract_dependency_name(reason: str) -> str | None:
    """Extract dependency name from error reason.

    Args:
        reason: Error reason string that may contain dependency name

    Returns:
        Extracted dependency name or None if not found
    """
    patterns = [
        r"dependency ['\"]([\w-]+)['\"]",
        r"missing ['\"]([\w-]+)['\"]",
        r"requires ['\"]([\w-]+)['\"]",
        r"['\"]([\w-]+)['\"] is not installed",
        r"['\"]([\w-]+)['\"] not found",
    ]
    for pattern in patterns:
        match = re.search(pattern, reason, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def _suggest_alternatives(format_id: str) -> list[str]:
    """Suggest alternative formats for a given format.

    Args:
        format_id: Format identifier

    Returns:
        List of alternative format identifiers
    """
    alternatives: dict[str, list[str]] = {
        "parquet": ["csv", "jsonl", "arrow"],
        "arrow": ["parquet", "csv", "jsonl"],
        "orc": ["parquet", "arrow"],
        "zstd": ["gzip", "bzip2", "xz"],
        "lz4": ["gzip", "bzip2"],
    }
    return alternatives.get(format_id, [])


class ErrorGuidance:
    """Helper class for generating actionable error guidance."""

    @staticmethod
    def format_not_supported(format_id: str, reason: str | None) -> str:
        """Generate guidance for FormatNotSupportedError.

        Args:
            format_id: Format identifier that is not supported
            reason: Optional reason why format is not supported

        Returns:
            Actionable guidance string
        """
        guidance = []

        # Check if it's a dependency issue
        if reason and "dependency" in reason.lower():
            dep_name = _extract_dependency_name(reason)
            if dep_name:
                guidance.append("To fix this issue:")
                guidance.append("1. Install the required dependency:")
                guidance.append(f"   pip install {dep_name}")
                guidance.append("")
                guidance.append("2. Verify the installation:")
                # Handle package name variations (e.g., pyarrow vs pyarrow)
                import_name = dep_name.replace("-", "_")
                guidance.append(f"   python -c 'import {import_name}'")
                guidance.append("")
                guidance.append("3. Retry your operation")
                guidance.append("")
                guidance.append("If you continue to have issues:")
                guidance.append("- Check that you're using a compatible Python version")
                guidance.append("- Verify your pip installation is working correctly")
                guidance.append(f"- See documentation: https://iterabledata.io/docs/formats/{format_id}")

        # Check if format is not implemented
        elif reason and "not implemented" in reason.lower():
            guidance.append("This format is not yet implemented.")
            guidance.append("")
            guidance.append("Options:")
            guidance.append("1. Use a different format that's supported")
            guidance.append("2. Check if there's a plugin available")
            guidance.append("3. Request this format in the issue tracker")

        return "\n".join(guidance) if guidance else ""

    @staticmethod
    def format_detection_failed(filename: str | None, reason: str | None) -> str:
        """Generate guidance for FormatDetectionError.

        Args:
            filename: Optional filename that could not be detected
            reason: Optional reason why detection failed

        Returns:
            Actionable guidance string
        """
        guidance = []
        guidance.append("The file format could not be determined.")
        guidance.append("")

        if filename:
            ext = os.path.splitext(filename)[1]
            if ext:
                guidance.append(f"File extension '{ext}' is not recognized.")
            else:
                guidance.append("File has no extension.")

        guidance.append("")
        guidance.append("To fix this issue:")
        guidance.append("1. Specify the format explicitly:")
        guidance.append("   open_iterable('file', iterableargs={'format': 'csv'})")
        guidance.append("")
        guidance.append("2. Rename the file with a recognized extension:")
        guidance.append("   mv file file.csv")
        guidance.append("")
        guidance.append("3. Check the file content:")
        guidance.append("   - Verify the file is not corrupted")
        guidance.append("   - Ensure the file contains valid data")
        guidance.append("   - Check file encoding (use encoding parameter if needed)")
        guidance.append("")
        guidance.append("For a list of supported formats, see: https://iterabledata.io/docs/formats/")

        return "\n".join(guidance)

    @staticmethod
    def format_parse_error(
        format_id: str,
        message: str,
        filename: str | None,
        row_number: int | None,
        byte_offset: int | None,
        original_line: str | None,
    ) -> str:
        """Generate guidance for FormatParseError.

        Args:
            format_id: Format identifier
            message: Error message describing the parse failure
            filename: Optional filename where error occurred
            row_number: Optional row number
            byte_offset: Optional byte offset
            original_line: Optional original line content

        Returns:
            Actionable guidance string
        """
        guidance = []
        guidance.append("This usually means:")

        # Analyze error message to provide specific guidance
        if "delimiter" in message.lower() or "csv" in format_id.lower():
            guidance.append("- The file has inconsistent delimiters")
            guidance.append("- There's an unescaped quote or special character")
            guidance.append("- The file encoding is incorrect")
            guidance.append("")
            guidance.append("To fix this issue:")
            guidance.append("1. Check the problematic line:")
            if row_number:
                guidance.append(f"   - Open the file and examine line {row_number}")
            guidance.append("   - Look for unescaped quotes, commas, or special characters")
            guidance.append("   - Verify the delimiter matches your expectations")
            guidance.append("")
            guidance.append("2. Specify the correct delimiter:")
            guidance.append("   open_iterable('file.csv', iterableargs={'delimiter': ';'})")
            guidance.append("")
            guidance.append("3. Handle encoding issues:")
            guidance.append("   open_iterable('file.csv', iterableargs={'encoding': 'utf-8'})")
            guidance.append("")
            guidance.append("4. Use error handling to skip problematic rows:")
            guidance.append("   open_iterable('file.csv', iterableargs={'on_error': 'skip'})")

        elif "json" in message.lower() or "parse" in message.lower() or "json" in format_id.lower():
            guidance.append("- The JSON structure is invalid")
            guidance.append("- There's a syntax error in the JSON")
            guidance.append("- The file encoding is incorrect")
            guidance.append("")
            guidance.append("To fix this issue:")
            guidance.append("1. Validate the JSON:")
            guidance.append("   python -m json.tool file.json")
            guidance.append("")
            guidance.append("2. Check the problematic line:")
            if row_number:
                guidance.append(f"   - Examine line {row_number} in the file")
            if original_line:
                line_preview = original_line[:100] + ("..." if len(original_line) > 100 else "")
                guidance.append(f"   - Problematic line: {line_preview}")
            guidance.append("")
            guidance.append("3. Use error handling to skip problematic rows:")
            guidance.append("   open_iterable('file.jsonl', iterableargs={'on_error': 'skip'})")

        guidance.append("")
        guidance.append(f"For more help, see: https://iterabledata.io/docs/formats/{format_id}#error-handling")

        return "\n".join(guidance)

    @staticmethod
    def codec_not_supported(codec_name: str, reason: str | None) -> str:
        """Generate guidance for CodecNotSupportedError.

        Args:
            codec_name: Codec name that is not supported
            reason: Optional reason why codec is not supported

        Returns:
            Actionable guidance string
        """
        guidance = []

        # Check if it's a dependency issue
        if reason and "dependency" in reason.lower():
            dep_name = _extract_dependency_name(reason)
            if dep_name:
                guidance.append("To fix this issue:")
                guidance.append("1. Install the required dependency:")
                guidance.append(f"   pip install {dep_name}")
                guidance.append("")
                guidance.append("2. Verify the installation:")
                import_name = dep_name.replace("-", "_")
                guidance.append(f"   python -c 'import {import_name}'")
                guidance.append("")
                guidance.append("3. Retry your operation")
                guidance.append("")

        # Suggest alternatives
        alternatives = _suggest_alternatives(codec_name)
        if alternatives:
            guidance.append("Alternative: Use a different compression format that's already installed:")
            for alt in alternatives:
                guidance.append(f"- {alt.capitalize()} (.{alt}): Usually pre-installed")
            guidance.append("")

        guidance.append("For more information, see: https://iterabledata.io/docs/compression")

        return "\n".join(guidance)

    @staticmethod
    def stream_not_seekable(operation: str | None) -> str:
        """Generate guidance for StreamNotSeekableError.

        Args:
            operation: Optional operation that requires seeking

        Returns:
            Actionable guidance string
        """
        guidance = []
        guidance.append("The stream you're trying to reset doesn't support seeking. This typically happens with:")
        guidance.append("- Standard input (stdin)")
        guidance.append("- Network streams (HTTP, FTP)")
        guidance.append("- Pipes and other non-seekable streams")
        guidance.append("")
        guidance.append("To fix this issue:")
        guidance.append("1. If reading from a file, ensure the file is opened in a seekable mode")
        guidance.append("2. If reading from stdin, consider reading the data into memory first")
        guidance.append("3. If reading from a network stream, download the file first, then process it")
        if operation:
            guidance.append(f"4. Avoid calling {operation}() on non-seekable streams")
        else:
            guidance.append("4. Avoid calling reset() on non-seekable streams")
        guidance.append("")
        guidance.append("Alternative: Read the stream once and process it without resetting")
        guidance.append("")
        guidance.append(
            "For more information, see: https://iterabledata.io/docs/getting-started/troubleshooting#reset-operation-issues"
        )

        return "\n".join(guidance)
