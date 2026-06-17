"""Actionable error guidance strings for IterableData exceptions."""

from __future__ import annotations

import os
import re


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
