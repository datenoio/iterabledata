"""
Dataset inspection operations.

Provides functions for inspecting datasets: counting rows, getting samples,
detecting headers, sniffing file formats, and analyzing structure.
"""

from __future__ import annotations

import collections.abc
from collections import deque
from collections.abc import Iterator
from typing import Any

from ..helpers.detect import detect_file_type, open_iterable
from ..types import Row


def count(iterable: collections.abc.Iterable[Row], engine: str | None = None) -> int:
    """
    Count the total number of rows in an iterable dataset.

    Uses DuckDB engine for fast counting on supported formats (CSV, JSONL, JSON, Parquet)
    when available. Falls back to Python streaming iteration otherwise.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        engine: Optional engine to use ('duckdb' for optimization)

    Returns:
        Total number of rows as an integer

    Example:
        >>> from iterable.ops import inspect
        >>> count = inspect.count("data.csv", engine="duckdb")  # doctest: +SKIP
        >>> print(f"Total rows: {count}")  # doctest: +SKIP
    """
    # If it's a string (file path), try to use DuckDB for fast counting
    if isinstance(iterable, str) and engine == "duckdb":
        try:
            with open_iterable(iterable, engine="duckdb") as source:
                if hasattr(source, "totals"):
                    total = source.totals()
                    if total is not None:
                        return total
        except Exception:
            # Fall back to Python iteration if DuckDB fails
            pass

    # Python fallback: iterate and count
    if isinstance(iterable, str):
        # It's a file path, open it
        with open_iterable(iterable) as source:
            return sum(1 for _ in source)
    else:
        # It's already an iterable
        return sum(1 for _ in iterable)


def head(iterable: collections.abc.Iterable[Row], n: int = 10) -> Iterator[Row]:
    """
    Get the first N rows from an iterable dataset.

    Returns an iterator that yields the first N rows without consuming
    the entire iterable.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        n: Number of rows to return (default: 10)

    Yields:
        Row dictionaries (first N rows)

    Example:
        >>> from iterable.ops import inspect
        >>> for row in inspect.head("data.csv", n=5):  # doctest: +SKIP
        ...     print(row)
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    count = 0
    for row in iterable:
        if count >= n:
            break
        yield row
        count += 1


def tail(iterable: collections.abc.Iterable[Row], n: int = 10) -> list[Row]:
    """
    Get the last N rows from an iterable dataset.

    Returns a list containing the last N rows. For large datasets, this
    may require iterating through the entire dataset.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        n: Number of rows to return (default: 10)

    Returns:
        List of row dictionaries (last N rows)

    Example:
        >>> from iterable.ops import inspect
        >>> last_rows = inspect.tail("data.csv", n=5)  # doctest: +SKIP
        >>> print(last_rows)  # doctest: +SKIP
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    # Use deque with maxlen for efficient tail collection
    tail_buffer = deque(maxlen=n)
    for row in iterable:
        tail_buffer.append(row)

    return list(tail_buffer)


def headers(iterable: collections.abc.Iterable[Row], limit: int | None = None) -> list[str]:
    """
    Get column names (headers) from an iterable dataset.

    Extracts column names from the first row's keys. Optionally limits
    the number of rows examined for header detection.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        limit: Optional limit on number of rows to examine (default: None, uses first row)

    Returns:
        List of column names (field names)

    Example:
        >>> from iterable.ops import inspect
        >>> cols = inspect.headers("data.csv")  # doctest: +SKIP
        >>> print(f"Columns: {cols}")  # doctest: +SKIP
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    # Get headers from first row
    try:
        first_row = next(iter(iterable))
        if isinstance(first_row, dict):
            return list(first_row.keys())
        else:
            return []
    except StopIteration:
        # Empty dataset
        return []


def sniff(filename: str) -> dict[str, Any]:
    """
    Detect file format, encoding, compression, and other metadata.

    Analyzes a file to determine its format, encoding, delimiter (for CSV),
    compression, and whether it has a header row.

    Args:
        filename: Path to the file to analyze

    Returns:
        Dictionary containing:
        - format: detected format (e.g., "csv", "jsonl")
        - encoding: detected encoding (e.g., "utf-8")
        - delimiter: detected delimiter for CSV (e.g., ",")
        - compression: detected compression (e.g., "gzip" or None)
        - has_header: boolean indicating if header row exists

    Example:
        >>> from iterable.ops import inspect
        >>> info = inspect.sniff("data.csv.gz")  # doctest: +SKIP
        >>> print(f"Format: {info['format']}, Compression: {info['compression']}")  # doctest: +SKIP
    """
    # Use existing detect_file_type function
    file_type_info = detect_file_type(filename)

    # detect_file_type returns the datatype/codec as classes (exposing a static
    # id()), not plain strings, so resolve them to format/compression names here.
    def _id_of(cls: Any) -> str | None:
        if cls is None:
            return None
        id_attr = getattr(cls, "id", None)
        if callable(id_attr):
            try:
                return id_attr()
            except Exception:
                return None
        return None

    datatype_cls = file_type_info.get("datatype")
    codec_cls = file_type_info.get("codec")

    result: dict[str, Any] = {
        "format": _id_of(datatype_cls) or "unknown",
        "encoding": file_type_info.get("encoding", "utf-8"),
        "compression": _id_of(codec_cls),
        "has_header": None,  # Will be determined by opening the file
    }

    # Try to detect delimiter and header for CSV files
    if result["format"] == "csv":
        try:
            with open_iterable(filename) as source:
                # Check if first row looks like headers
                first_row = next(iter(source), None)
                if first_row:
                    # Simple heuristic: if first row values are all strings and look like headers
                    result["has_header"] = all(
                        isinstance(v, str) and v.replace("_", "").replace("-", "").isalnum() for v in first_row.values()
                    )
                    # Try to detect delimiter from first line if available
                    # This is a simplified approach
                    result["delimiter"] = ","  # Default, could be enhanced
        except Exception:
            pass

    return result


def analyze(
    iterable: collections.abc.Iterable[Row],
    autodoc: bool = False,
    sample_size: int = 10000,
) -> dict[str, Any]:
    """
    Analyze dataset structure, field types, and generate metadata.

    Performs comprehensive analysis of a dataset including:
    - Row count (if calculable)
    - Field names and types
    - Nullability information
    - Sample values

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        autodoc: Whether to include AI-powered documentation (requires AI dependencies)
        sample_size: Number of rows to sample for analysis (default: 10000)

    Returns:
        Dictionary containing:
        - row_count: total number of rows (if calculable)
        - fields: dictionary mapping field names to metadata
        - structure: overall structure information

    Example:
        >>> from iterable.ops import inspect
        >>> analysis = inspect.analyze("data.csv")  # doctest: +SKIP
        >>> print(f"Fields: {list(analysis['fields'].keys())}")  # doctest: +SKIP
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    fields: dict[str, dict[str, Any]] = {}
    row_count = 0
    sample_values: dict[str, list[Any]] = {}

    # Sample rows for analysis
    for i, row in enumerate(iterable):
        if i >= sample_size:
            break

        row_count = i + 1

        # Analyze each field
        for field_name, value in row.items():
            if field_name not in fields:
                fields[field_name] = {
                    "type": _infer_type(value),
                    "nullable": value is None,
                    "sample_values": [],
                }
                sample_values[field_name] = []

            # Update nullability
            if value is None:
                fields[field_name]["nullable"] = True

            # Collect sample values (up to 5 per field)
            if len(sample_values[field_name]) < 5 and value is not None:
                sample_values[field_name].append(value)

    # Add sample values to field metadata
    for field_name, samples in sample_values.items():
        fields[field_name]["sample_values"] = samples

    result: dict[str, Any] = {
        "row_count": row_count if row_count < sample_size else None,
        "fields": fields,
        "structure": {
            "field_count": len(fields),
            "analyzed_rows": row_count,
        },
    }

    # Add AI documentation if requested
    if autodoc:
        try:
            from ..ai import doc  # noqa: F401

            # Generate documentation for fields
            # This would call ai.doc.generate() with schema information
            # For now, we'll skip this as AI module isn't implemented yet
            pass
        except ImportError:
            pass

    return result


def _infer_type(value: Any) -> str:
    """Infer Python type name from a value."""
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "bool"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        return "str"
    elif isinstance(value, (list, tuple)):
        return "list"
    elif isinstance(value, dict):
        return "dict"
    else:
        return type(value).__name__
