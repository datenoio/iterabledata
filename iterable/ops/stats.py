"""
Statistics operations for data analysis.

Provides functions for computing statistics, frequency analysis,
and unique value detection.
"""

from __future__ import annotations

import collections.abc
from collections import Counter
from typing import Any

from ..helpers.detect import open_iterable
from ..helpers.utils import hashable_key, hashable_repr
from ..types import Row


def compute(
    iterable: collections.abc.Iterable[Row],
    detect_dates: bool = False,
    engine: str | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Compute comprehensive statistics for all fields in an iterable dataset.

    Uses DuckDB engine for fast computation on supported formats when available.
    Falls back to Python streaming iteration otherwise.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        detect_dates: Whether to detect date fields (default: False)
        engine: Optional engine to use ('duckdb' for optimization)

    Returns:
        Dictionary mapping field names to their statistics:
        - count: number of non-null values
        - null_count: number of null values
        - unique_count: number of unique values
        - min, max: minimum and maximum values (for numeric/date fields)
        - mean, median, stddev: statistical measures (for numeric fields)

    Example:
        >>> from iterable.ops import stats
        >>> summary = stats.compute("data.csv", detect_dates=True)
        >>> print(summary["price"]["mean"])
    """
    if isinstance(iterable, str) and engine == "duckdb":
        # Try DuckDB optimization for supported formats
        try:
            with open_iterable(iterable, engine="duckdb") as _:
                # For now, fall back to Python implementation
                # DuckDB-specific stats computation can be added later
                pass
        except Exception:
            pass

    # Python fallback: compute statistics by iterating
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    field_stats: dict[str, dict[str, Any]] = {}
    row_count = 0

    for row in iterable:
        row_count += 1
        for field_name, value in row.items():
            if field_name not in field_stats:
                field_stats[field_name] = {
                    "count": 0,
                    "null_count": 0,
                    "values": [],
                    "numeric_values": [],
                }

            stats = field_stats[field_name]

            if value is None:
                stats["null_count"] += 1
            else:
                stats["count"] += 1
                stats["values"].append(value)

                # Collect numeric values for statistical computation
                if isinstance(value, (int, float)):
                    stats["numeric_values"].append(value)

    # Compute final statistics
    result: dict[str, dict[str, Any]] = {}
    for field_name, stats in field_stats.items():
        values = stats["values"]
        numeric_values = stats["numeric_values"]

        field_result: dict[str, Any] = {
            "count": stats["count"],
            "null_count": stats["null_count"],
            "unique_count": len({hashable_repr(v) for v in values}),
        }

        # Numeric statistics
        if numeric_values:
            sorted_numeric = sorted(numeric_values)
            field_result["min"] = sorted_numeric[0]
            field_result["max"] = sorted_numeric[-1]
            field_result["mean"] = sum(numeric_values) / len(numeric_values)

            # Median
            n = len(sorted_numeric)
            if n % 2 == 0:
                field_result["median"] = (sorted_numeric[n // 2 - 1] + sorted_numeric[n // 2]) / 2
            else:
                field_result["median"] = sorted_numeric[n // 2]

            # Standard deviation
            if len(numeric_values) > 1:
                mean = field_result["mean"]
                variance = sum((x - mean) ** 2 for x in numeric_values) / len(numeric_values)
                field_result["stddev"] = variance**0.5
            else:
                field_result["stddev"] = 0.0

        # String statistics
        string_values = [v for v in values if isinstance(v, str)]
        if string_values:
            field_result["min_length"] = min(len(v) for v in string_values)
            field_result["max_length"] = max(len(v) for v in string_values)
            field_result["avg_length"] = sum(len(v) for v in string_values) / len(string_values)

        result[field_name] = field_result

    return result


def frequency(
    iterable: collections.abc.Iterable[Row],
    fields: list[str] | None = None,
    limit: int | None = None,
) -> dict[str, dict[Any, int]]:
    """
    Compute frequency distributions for specified fields.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        fields: List of field names to analyze (None for all fields)
        limit: Optional limit on number of top frequencies to return per field

    Returns:
        Dictionary mapping field names to frequency dictionaries
        (value -> count, sorted by frequency descending)

    Example:
        >>> from iterable.ops import stats
        >>> freq = stats.frequency("data.csv", fields=["status"])
        >>> print(freq["status"]["active"])  # Count of "active" status
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    field_counters: dict[str, Counter[Any]] = {}

    for row in iterable:
        for field_name, value in row.items():
            if fields is not None and field_name not in fields:
                continue

            if field_name not in field_counters:
                field_counters[field_name] = Counter()

            # Use value as key when hashable, else string repr (so list/dict work)
            key = hashable_key(value)
            field_counters[field_name][key] += 1

    # Convert to dictionaries and apply limit
    result: dict[str, dict[Any, int]] = {}
    for field_name, counter in field_counters.items():
        most_common = counter.most_common(limit) if limit else counter.most_common()
        result[field_name] = dict(most_common)

    return result


def uniq(
    iterable: collections.abc.Iterable[Row],
    fields: list[str] | None = None,
    values_only: bool = False,
    include_count: bool = False,
) -> collections.abc.Iterable[Row | Any] | dict[Any, int]:
    """
    Identify unique rows or unique values for specified fields.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        fields: List of field names to use for uniqueness (None for all fields)
        values_only: If True, return only unique values (not full rows)
        include_count: If True, include occurrence counts in results

    Returns:
        - If values_only=True: iterator of unique values
        - If include_count=True: dictionary mapping unique items to counts
        - Otherwise: iterator of unique rows

    Example:
        >>> from iterable.ops import stats
        >>> unique_emails = list(stats.uniq("data.csv", fields=["email"], values_only=True))
        >>> print(f"Unique emails: {len(unique_emails)}")
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    # When include_count=True, return a dict directly (no generator)
    if include_count:
        return _uniq_counts(iterable, fields, values_only)

    return _uniq_iter(iterable, fields, values_only)


def _uniq_counts(
    iterable: collections.abc.Iterable[Row],
    fields: list[str] | None,
    values_only: bool,
) -> dict[Any, int]:
    """Build unique counts dict (no yield, so caller gets a real dict)."""
    seen: set[str] = set()
    counts: dict[str, int] = {}
    seen_items: dict[str, Any] = {}

    for row in iterable:
        key = hashable_repr(tuple(row.get(f) for f in fields)) if fields else hashable_repr(tuple(sorted(row.items())))
        if key not in seen:
            seen.add(key)
            if values_only:
                if fields and len(fields) == 1:
                    seen_items[key] = row[fields[0]]
                elif fields:
                    seen_items[key] = tuple(row.get(f) for f in fields)
                else:
                    seen_items[key] = tuple(sorted(row.items()))
            else:
                seen_items[key] = row
            counts[key] = 1
        else:
            counts[key] += 1

    result: dict[Any, int] = {}
    for k, c in counts.items():
        item = seen_items[k]
        try:
            hash(item)
            key = item
        except TypeError:
            key = hashable_repr(item)
        result[key] = c
    return result


def _uniq_iter(
    iterable: collections.abc.Iterable[Row],
    fields: list[str] | None,
    values_only: bool,
) -> collections.abc.Iterator[Row | Any]:
    """Yield unique rows/values (generator)."""
    seen: set[str] = set()
    for row in iterable:
        key = hashable_repr(tuple(row.get(f) for f in fields)) if fields else hashable_repr(tuple(sorted(row.items())))
        if key not in seen:
            seen.add(key)
            if values_only:
                if fields and len(fields) == 1:
                    yield row[fields[0]]
                elif fields:
                    yield tuple(row.get(f) for f in fields)
                else:
                    yield tuple(sorted(row.items()))
            else:
                yield row
