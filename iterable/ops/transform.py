"""
Row and column transformation operations.

Provides functions for transforming data: slicing, sampling, deduplication,
selection, and other row/column operations.
"""

from __future__ import annotations

import collections.abc
import random
import re
import uuid
from collections import deque
from collections.abc import Iterator
from typing import Any

from ..helpers.detect import open_iterable
from ..helpers.utils import hashable_repr
from ..types import Row


def head(iterable: collections.abc.Iterable[Row], n: int = 10) -> Iterator[Row]:
    """
    Get the first N rows from an iterable dataset.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        n: Number of rows to return (default: 10)

    Yields:
        Row dictionaries (first N rows)

    Example:
        >>> from iterable.ops import transform
        >>> for row in transform.head("data.csv", n=5):
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

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        n: Number of rows to return (default: 10)

    Returns:
        List of row dictionaries (last N rows)

    Example:
        >>> from iterable.ops import transform
        >>> last_rows = transform.tail("data.csv", n=5)
    """

    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    tail_buffer = deque(maxlen=n)
    for row in iterable:
        tail_buffer.append(row)

    return list(tail_buffer)


def sample_rows(
    iterable: collections.abc.Iterable[Row],
    n: int = 1000,
    seed: int | None = None,
) -> Iterator[Row]:
    """
    Randomly sample rows from an iterable dataset.

    Uses reservoir sampling for efficient sampling without materializing
    the entire dataset.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        n: Number of rows to sample (default: 1000)
        seed: Optional random seed for reproducibility

    Yields:
        Randomly sampled row dictionaries

    Example:
        >>> from iterable.ops import transform
        >>> for row in transform.sample_rows("data.csv", n=100, seed=42):
        ...     print(row)
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    if seed is not None:
        random.seed(seed)

    # Reservoir sampling algorithm
    reservoir: list[Row] = []
    count = 0

    for row in iterable:
        count += 1
        if len(reservoir) < n:
            reservoir.append(row)
        else:
            # Randomly replace an element in reservoir
            j = random.randint(0, count - 1)
            if j < n:
                reservoir[j] = row

    # Yield sampled rows
    for row in reservoir:
        yield row


def deduplicate(
    iterable: collections.abc.Iterable[Row],
    keys: list[str] | None = None,
    keep: str = "first",
) -> Iterator[Row]:
    """
    Remove duplicate rows based on specified key fields.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        keys: List of field names to use for uniqueness (None for all fields)
        keep: Which occurrence to keep - "first" (default) or "last"

    Yields:
        Deduplicated row dictionaries

    Example:
        >>> from iterable.ops import transform
        >>> for row in transform.deduplicate("data.csv", keys=["email"]):
        ...     print(row)
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    seen: set[str] = set()
    seen_list: list[Row] = []  # For "last" strategy

    for row in iterable:
        # Hashable key (handles list/dict values in row)
        key = hashable_repr(_get_key(row, keys))

        if keep == "first":
            if key not in seen:
                seen.add(key)
                yield row
        else:  # keep == "last"
            if key in seen:
                # Remove previous occurrence
                seen_list = [r for r in seen_list if hashable_repr(_get_key(r, keys)) != key]
            seen.add(key)
            seen_list.append(row)

    if keep == "last":
        # Yield all rows from seen_list
        for row in seen_list:
            yield row


def _get_key(row: Row, keys: list[str] | None) -> tuple[Any, ...]:
    """Get uniqueness key from a row."""
    if keys:
        return tuple(row.get(k) for k in keys)
    else:
        return tuple(sorted(row.items()))


def select(
    iterable: collections.abc.Iterable[Row],
    fields: list[str] | dict[str, str] | None = None,
) -> Iterator[Row]:
    """
    Select specific columns from rows, optionally with renaming.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        fields: List of field names to select, or dict mapping old->new names

    Yields:
        Row dictionaries with only selected fields

    Example:
        >>> from iterable.ops import transform
        >>> # Select specific fields
        >>> for row in transform.select("data.csv", fields=["id", "name"]):
        ...     print(row)
        >>> # Select and rename
        >>> for row in transform.select("data.csv", fields={"old_name": "new_name"}):
        ...     print(row)
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    for row in iterable:
        if fields is None:
            yield row
        elif isinstance(fields, list):
            # Select specific fields
            selected = {k: row.get(k) for k in fields}
            yield selected
        elif isinstance(fields, dict):
            # Rename fields
            renamed = {new_name: row.get(old_name) for old_name, new_name in fields.items()}
            yield renamed


def slice_rows(
    iterable: collections.abc.Iterable[Row],
    start: int = 0,
    end: int | None = None,
) -> Iterator[Row]:
    """
    Slice rows by index range.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        start: Start index (inclusive, default: 0)
        end: End index (exclusive, None for all remaining rows)

    Yields:
        Row dictionaries in the specified range

    Example:
        >>> from iterable.ops import transform
        >>> for row in transform.slice_rows("data.csv", start=100, end=200):
        ...     print(row)
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    for i, row in enumerate(iterable):
        if i < start:
            continue
        if end is not None and i >= end:
            break
        yield row


def enum_field(
    iterable: collections.abc.Iterable[Row],
    field: str = "id",
    type: str = "int",
    start: int = 0,
) -> Iterator[Row]:
    """
    Add sequence numbers or enumeration to rows.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        field: Name of the field to add (default: "id")
        type: Type of enumeration - "int" for sequence numbers, "uuid" for UUIDs (default: "int")
        start: Starting value for integer enumeration (default: 0)

    Yields:
        Row dictionaries with added enumeration field

    Example:
        >>> from iterable.ops import transform
        >>> # Add sequence numbers
        >>> for row in transform.enum_field("data.csv", field="seq_id", type="int"):
        ...     print(row)
        >>> # Add UUIDs
        >>> for row in transform.enum_field("data.csv", field="id", type="uuid"):
        ...     print(row)
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    counter = start
    for row in iterable:
        new_row = row.copy()
        if type == "uuid":
            new_row[field] = str(uuid.uuid4())
        else:  # type == "int"
            new_row[field] = counter
            counter += 1
        yield new_row


def reverse(iterable: collections.abc.Iterable[Row]) -> Iterator[Row]:
    """
    Reverse the order of rows.

    Note: This requires materializing all rows in memory.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream

    Yields:
        Row dictionaries in reverse order

    Example:
        >>> from iterable.ops import transform
        >>> for row in transform.reverse("data.csv"):
        ...     print(row)
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    # Materialize all rows
    rows = list(iterable)
    # Yield in reverse
    yield from reversed(rows)


def fill_missing(
    iterable: collections.abc.Iterable[Row],
    field: str,
    strategy: str = "forward",
    value: Any = None,
) -> Iterator[Row]:
    """
    Fill missing/null values in a field.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        field: Name of the field to fill
        strategy: Filling strategy - "forward", "backward", or "constant" (default: "forward")
        value: Constant value to use when strategy="constant"

    Yields:
        Row dictionaries with filled missing values

    Example:
        >>> from iterable.ops import transform
        >>> # Forward fill
        >>> for row in transform.fill_missing("data.csv", field="status", strategy="forward"):
        ...     print(row)
        >>> # Fill with constant
        >>> for row in transform.fill_missing("data.csv", field="category", value="unknown"):
        ...     print(row)
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    if strategy == "constant":
        # Simple constant fill
        for row in iterable:
            new_row = row.copy()
            if new_row.get(field) is None or (
                isinstance(new_row.get(field), str) and len(new_row.get(field, "").strip()) == 0
            ):
                new_row[field] = value
            yield new_row
    elif strategy == "forward":
        # Forward fill: use last valid value
        last_value = None
        for row in iterable:
            new_row = row.copy()
            current_value = new_row.get(field)
            if current_value is None or (isinstance(current_value, str) and len(current_value.strip()) == 0):
                if last_value is not None:
                    new_row[field] = last_value
            else:
                last_value = current_value
            yield new_row
    elif strategy == "backward":
        # Backward fill: need to materialize to go backwards
        rows = list(iterable)
        next_value = None
        for row in reversed(rows):
            current_value = row.get(field)
            if current_value is None or (isinstance(current_value, str) and len(current_value.strip()) == 0):
                if next_value is not None:
                    row[field] = next_value
            else:
                next_value = current_value
        for row in rows:
            yield row
    else:
        raise ValueError(f"Unknown fill strategy: {strategy}")


def rename_fields(
    iterable: collections.abc.Iterable[Row],
    mapping: dict[str, str],
) -> Iterator[Row]:
    """
    Rename fields in rows.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        mapping: Dictionary mapping old field names to new field names

    Yields:
        Row dictionaries with renamed fields

    Example:
        >>> from iterable.ops import transform
        >>> for row in transform.rename_fields("data.csv", {"old_name": "new_name"}):
        ...     print(row)
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    for row in iterable:
        new_row = {}
        for key, val in row.items():
            if key in mapping:
                new_row[mapping[key]] = val
            else:
                new_row[key] = val
        yield new_row


def explode(
    iterable: collections.abc.Iterable[Row],
    field: str,
    separator: str | None = None,
) -> Iterator[Row]:
    """
    Explode array or delimited string fields into multiple rows.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        field: Name of the field to explode
        separator: Separator for string fields (None for array fields)

    Yields:
        Row dictionaries with exploded field (one row per value)

    Example:
        >>> from iterable.ops import transform
        >>> # Explode array field
        >>> for row in transform.explode("data.jsonl", field="tags"):
        ...     print(row)
        >>> # Explode delimited string
        >>> for row in transform.explode("data.csv", field="categories", separator=","):
        ...     print(row)
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    for row in iterable:
        value = row.get(field)
        if value is None:
            yield row
            continue

        # Handle array/list
        if isinstance(value, (list, tuple)):
            for item in value:
                new_row = row.copy()
                new_row[field] = item
                yield new_row
        # Handle delimited string
        elif isinstance(value, str) and separator:
            parts = [p.strip() for p in value.split(separator) if p.strip()]
            for part in parts:
                new_row = row.copy()
                new_row[field] = part
                yield new_row
        else:
            # Single value, yield as-is
            yield row


def replace_values(
    iterable: collections.abc.Iterable[Row],
    field: str,
    pattern: str,
    replacement: str,
    regex: bool = False,
) -> Iterator[Row]:
    """
    Replace values in a field based on patterns or exact matches.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        field: Name of the field to replace values in
        pattern: Pattern to match (exact string or regex pattern)
        replacement: Replacement string
        regex: Whether pattern is a regex (default: False)

    Yields:
        Row dictionaries with replaced values

    Example:
        >>> from iterable.ops import transform
        >>> # Simple replacement
        >>> for row in transform.replace_values("data.csv", field="status", pattern="old", replacement="new"):
        ...     print(row)
        >>> # Regex replacement
        >>> for row in transform.replace_values(
        ...     "data.csv", field="text", pattern=r"\\d+", replacement="NUMBER", regex=True
        ... ):
        ...     print(row)
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    if regex:
        compiled_pattern = re.compile(pattern)

    for row in iterable:
        new_row = row.copy()
        value = new_row.get(field)
        if value is not None and isinstance(value, str):
            if regex:
                new_row[field] = compiled_pattern.sub(replacement, value)
            else:
                new_row[field] = value.replace(pattern, replacement)
        yield new_row


def sort_rows(
    iterable: collections.abc.Iterable[Row],
    by: list[str],
    desc: list[bool] | bool = False,
) -> Iterator[Row]:
    """
    Sort rows by specified fields.

    Note: This requires materializing all rows in memory.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        by: List of field names to sort by
        desc: List of booleans indicating descending order per field, or single boolean for all fields (default: False)

    Yields:
        Row dictionaries in sorted order

    Example:
        >>> from iterable.ops import transform
        >>> # Sort by single field
        >>> for row in transform.sort_rows("data.csv", by=["date"]):
        ...     print(row)
        >>> # Sort by multiple fields
        >>> for row in transform.sort_rows("data.csv", by=["status", "id"], desc=[True, False]):
        ...     print(row)
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    # Materialize rows
    rows = list(iterable)

    # Normalize desc to list
    if isinstance(desc, bool):
        desc = [desc] * len(by)
    elif len(desc) != len(by):
        desc = desc + [False] * (len(by) - len(desc))

    # Sort function
    def sort_key(row: Row) -> tuple[Any, ...]:
        key_parts = []
        for i, field in enumerate(by):
            value = row.get(field)
            # Handle None values
            if value is None:
                value = float("inf") if desc[i] else float("-inf")
            key_parts.append(value)
        return tuple(key_parts)

    # Sort rows
    sorted_rows = sorted(rows, key=sort_key, reverse=any(desc))

    # Yield sorted rows
    yield from sorted_rows


def transpose(iterable: collections.abc.Iterable[Row]) -> Iterator[Row]:
    """
    Transpose rows and columns.

    Note: This requires materializing all rows in memory.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream

    Yields:
        Transposed row dictionaries (rows become columns, columns become rows)

    Example:
        >>> from iterable.ops import transform
        >>> for row in transform.transpose("data.csv"):
        ...     print(row)
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    # Materialize rows
    rows = list(iterable)
    if not rows:
        return

    # Get all unique field names
    all_fields = set()
    for row in rows:
        all_fields.update(row.keys())

    # Transpose: each original field becomes a row
    for field_name in all_fields:
        transposed_row: Row = {}
        for i, original_row in enumerate(rows):
            transposed_row[f"row_{i}"] = original_row.get(field_name)
        yield transposed_row


def split(
    iterable: collections.abc.Iterable[Row],
    field: str,
    separator: str,
    into: list[str],
    remove_original: bool = True,
) -> Iterator[Row]:
    """
    Split a field into multiple fields.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        field: Name of the field to split
        separator: Separator to split on
        into: List of new field names for split parts
        remove_original: Whether to remove the original field (default: True)

    Yields:
        Row dictionaries with split fields

    Example:
        >>> from iterable.ops import transform
        >>> for row in transform.split("data.csv", field="full_name", separator=" ", into=["first", "last"]):
        ...     print(row)
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    for row in iterable:
        new_row = row.copy()
        value = new_row.get(field)
        if value is not None and isinstance(value, str):
            parts = value.split(separator)
            # Pad or truncate to match 'into' length
            parts = (parts + [None] * len(into))[: len(into)]
            for i, new_field in enumerate(into):
                new_row[new_field] = parts[i].strip() if parts[i] else None
        else:
            # Fill with None if value is missing
            for new_field in into:
                new_row[new_field] = None

        if remove_original:
            new_row.pop(field, None)

        yield new_row


def fixlengths(
    iterable: collections.abc.Iterable[Row],
    lengths: dict[str, int],
    pad_char: str = " ",
) -> Iterator[Row]:
    """
    Fix field lengths by padding or truncating.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        lengths: Dictionary mapping field names to target lengths
        pad_char: Character to use for padding (default: " ")

    Yields:
        Row dictionaries with fixed field lengths

    Example:
        >>> from iterable.ops import transform
        >>> for row in transform.fixlengths("data.csv", lengths={"code": 10, "name": 50}):
        ...     print(row)
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    for row in iterable:
        new_row = row.copy()
        for field_name, target_length in lengths.items():
            value = new_row.get(field_name)
            if value is not None:
                value_str = str(value)
                if len(value_str) < target_length:
                    # Pad
                    new_row[field_name] = value_str + pad_char * (target_length - len(value_str))
                elif len(value_str) > target_length:
                    # Truncate
                    new_row[field_name] = value_str[:target_length]
        yield new_row


def cat(*iterables: collections.abc.Iterable[Row]) -> Iterator[Row]:
    """
    Concatenate multiple iterables.

    Args:
        *iterables: Variable number of iterables to concatenate

    Yields:
        Row dictionaries from all iterables in sequence

    Example:
        >>> from iterable.ops import transform
        >>> for row in transform.cat("file1.csv", "file2.csv", "file3.csv"):
        ...     print(row)
    """
    for iterable in iterables:
        if isinstance(iterable, str):
            iterable = open_iterable(iterable)

        yield from iterable


def join(
    left: collections.abc.Iterable[Row],
    right: collections.abc.Iterable[Row],
    on: list[str] | str,
    join_type: str = "inner",
) -> Iterator[Row]:
    """
    Join two iterables based on key fields.

    Args:
        left: Left iterable (or file path)
        right: Right iterable (or file path)
        on: Field name(s) to join on (single string or list of strings)
        join_type: Type of join - "inner", "left", "right", "outer" (default: "inner")

    Yields:
        Joined row dictionaries

    Example:
        >>> from iterable.ops import transform
        >>> for row in transform.join("users.csv", "orders.csv", on="user_id", join_type="left"):
        ...     print(row)
    """
    if isinstance(left, str):
        left = open_iterable(left)
    if isinstance(right, str):
        right = open_iterable(right)

    # Normalize 'on' to list
    if isinstance(on, str):
        on = [on]

    # Materialize right side for lookup (hashable key so list/dict join keys work)
    right_dict: dict[str, list[Row]] = {}
    for row in right:
        key = hashable_repr(tuple(row.get(f) for f in on))
        if key not in right_dict:
            right_dict[key] = []
        right_dict[key].append(row)

    # Process left side
    left_keys_seen: set[str] = set()

    for left_row in left:
        left_key = hashable_repr(tuple(left_row.get(f) for f in on))
        left_keys_seen.add(left_key)

        if left_key in right_dict:
            # Match found
            for right_row in right_dict[left_key]:
                # Merge rows
                merged = left_row.copy()
                # Add right row fields with prefix to avoid conflicts
                for k, v in right_row.items():
                    if k not in on:  # Don't duplicate join keys
                        merged[f"right_{k}"] = v
                yield merged
        elif join_type in ("left", "outer"):
            # No match, but include left row
            merged = left_row.copy()
            first_right = next(iter(right_dict.values()), [{}])[0] if right_dict else {}
            for k in first_right.keys():
                if k not in on:
                    merged[f"right_{k}"] = None
            yield merged

    # Handle right-only rows for outer join
    if join_type == "outer":
        for right_key, right_rows in right_dict.items():
            if right_key not in left_keys_seen:
                for right_row in right_rows:
                    merged: Row = {}
                    for k in on:
                        merged[k] = right_row.get(k)
                    for k, v in right_row.items():
                        if k not in on:
                            merged[f"right_{k}"] = v
                    yield merged


def diff(
    left: collections.abc.Iterable[Row],
    right: collections.abc.Iterable[Row],
    keys: list[str] | None = None,
) -> Iterator[Row]:
    """
    Compute set difference (rows in left but not in right).

    Args:
        left: Left iterable (or file path)
        right: Right iterable (or file path)
        keys: Field names to use for comparison (None for all fields)

    Yields:
        Row dictionaries present in left but not in right

    Example:
        >>> from iterable.ops import transform
        >>> for row in transform.diff("file1.csv", "file2.csv", keys=["id"]):
        ...     print(row)
    """
    if isinstance(left, str):
        left = open_iterable(left)
    if isinstance(right, str):
        right = open_iterable(right)

    # Build set of keys from right (hashable so list/dict values work)
    right_keys: set[str] = set()
    for row in right:
        key = hashable_repr(_get_key(row, keys))
        right_keys.add(key)

    # Yield rows from left not in right
    for row in left:
        key = hashable_repr(_get_key(row, keys))
        if key not in right_keys:
            yield row


def exclude(
    iterable: collections.abc.Iterable[Row],
    exclude_iterable: collections.abc.Iterable[Row],
    keys: list[str] | None = None,
) -> Iterator[Row]:
    """
    Exclude rows that match keys in another iterable.

    Args:
        iterable: Main iterable (or file path)
        exclude_iterable: Iterable with rows to exclude (or file path)
        keys: Field names to use for matching (None for all fields)

    Yields:
        Row dictionaries from main iterable that don't match exclude keys

    Example:
        >>> from iterable.ops import transform
        >>> for row in transform.exclude("all_users.csv", "deleted_users.csv", keys=["id"]):
        ...     print(row)
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)
    if isinstance(exclude_iterable, str):
        exclude_iterable = open_iterable(exclude_iterable)

    # Build set of exclude keys (hashable so list/dict values work)
    exclude_keys: set[str] = set()
    for row in exclude_iterable:
        key = hashable_repr(_get_key(row, keys))
        exclude_keys.add(key)

    # Yield rows not in exclude set
    for row in iterable:
        key = hashable_repr(_get_key(row, keys))
        if key not in exclude_keys:
            yield row


# Alias for backward compatibility with task specification
sample = sample_rows
