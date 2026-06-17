"""Utilities for building safe, bounded samples for LLM prompts."""

from __future__ import annotations

import collections.abc
import json
import re
from typing import Any

from ..helpers.detect import open_iterable
from ..types import Row

# Column-name heuristics for PII redaction (case-insensitive substring match).
_PII_COLUMN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"email", re.I),
    re.compile(r"e[-_]?mail", re.I),
    re.compile(r"phone", re.I),
    re.compile(r"mobile", re.I),
    re.compile(r"ssn", re.I),
    re.compile(r"social.?security", re.I),
    re.compile(r"password", re.I),
    re.compile(r"passwd", re.I),
    re.compile(r"credit.?card", re.I),
    re.compile(r"card.?number", re.I),
)

_REDACTED = "***"


def _row_char_estimate(row: Row) -> int:
    try:
        return len(json.dumps(row, default=str))
    except (TypeError, ValueError):
        return len(str(row))


def _is_pii_column(name: str, extra_fields: set[str] | None = None) -> bool:
    if extra_fields and name in extra_fields:
        return True
    return any(pattern.search(name) for pattern in _PII_COLUMN_PATTERNS)


def sample_for_llm(
    iterable: collections.abc.Iterable[Row] | str,
    *,
    max_rows: int = 10,
    max_tokens: int | None = None,
    strategy: str = "head",
) -> list[Row]:
    """
    Build a bounded sample of rows suitable for LLM prompts.

    Token budget uses a JSON character-length heuristic (not tokenizer-exact).
    """
    if max_rows < 1:
        return []

    char_budget = max_tokens * 4 if max_tokens is not None else None

    if isinstance(iterable, str):
        source = open_iterable(iterable)
        try:
            return _sample_from_iter(source, max_rows=max_rows, char_budget=char_budget, strategy=strategy)
        finally:
            if hasattr(source, "close"):
                source.close()
    return _sample_from_iter(iterable, max_rows=max_rows, char_budget=char_budget, strategy=strategy)


def _sample_from_iter(
    iterable: collections.abc.Iterable[Row],
    *,
    max_rows: int,
    char_budget: int | None,
    strategy: str,
) -> list[Row]:
    if strategy == "stratified":
        return _stratified_sample(iterable, max_rows=max_rows, char_budget=char_budget)
    return _head_sample(iterable, max_rows=max_rows, char_budget=char_budget)


def _head_sample(
    iterable: collections.abc.Iterable[Row],
    *,
    max_rows: int,
    char_budget: int | None,
) -> list[Row]:
    rows: list[Row] = []
    chars = 0
    for row in iterable:
        if len(rows) >= max_rows:
            break
        row_chars = _row_char_estimate(row)
        if char_budget is not None and rows and chars + row_chars > char_budget:
            break
        rows.append(row)
        chars += row_chars
    return rows


def _stratified_sample(
    iterable: collections.abc.Iterable[Row],
    *,
    max_rows: int,
    char_budget: int | None,
) -> list[Row]:
    buffer: list[Row] = []
    total_seen = 0
    for row in iterable:
        total_seen += 1
        if len(buffer) < max_rows * 3:
            buffer.append(row)
        elif total_seen % max(1, total_seen // max_rows) == 0 and len(buffer) < max_rows * 5:
            buffer.append(row)

    if len(buffer) <= max_rows:
        return _apply_char_budget(buffer, max_rows, char_budget)

    step = max(1, len(buffer) // max_rows)
    picked = [buffer[i] for i in range(0, len(buffer), step)][:max_rows]
    return _apply_char_budget(picked, max_rows, char_budget)


def _apply_char_budget(rows: list[Row], max_rows: int, char_budget: int | None) -> list[Row]:
    if char_budget is None:
        return rows[:max_rows]
    result: list[Row] = []
    chars = 0
    for row in rows:
        if len(result) >= max_rows:
            break
        row_chars = _row_char_estimate(row)
        if result and chars + row_chars > char_budget:
            break
        result.append(row)
        chars += row_chars
    return result


def redact_for_llm(
    rows: list[Row],
    *,
    pii_fields: list[str] | None = None,
) -> list[Row]:
    """
    Mask likely PII values in sample rows before external LLM calls.

    Uses column-name heuristics and optional explicit field names (e.g. from Metacrafter).
    """
    extra_fields = set(pii_fields or [])
    redacted: list[Row] = []
    for row in rows:
        if not isinstance(row, dict):
            redacted.append(row)
            continue
        new_row: dict[str, Any] = {}
        for key, value in row.items():
            if _is_pii_column(str(key), extra_fields):
                new_row[key] = _REDACTED
            else:
                new_row[key] = value
        redacted.append(new_row)
    return redacted


def pii_field_names_from_metacrafter(filename: str, field_names: list[str]) -> list[str] | None:
    """Return PII field names from Metacrafter when available."""
    from .semantic import detect_pii

    entries = detect_pii(filename, field_names)
    if not entries:
        return None
    return [str(entry["field"]) for entry in entries if entry.get("field")]
