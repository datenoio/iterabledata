"""Size-based sampling strategy for LLM documentation prompts.

Selects how many rows (and whether random rows) to send to the LLM based on the
input size, following the dataset-documentation service requirements:

- Small files (< 1 MB): full schema + first N rows.
- Medium files (1-20 MB): full schema + first N rows + N random rows.
- Large files (> 20 MB): schema and statistics only (no data rows).

``N`` defaults from the ``MAX_ROWS_SAMPLING`` environment variable.
"""

from __future__ import annotations

import collections.abc
import os
import random
from dataclasses import dataclass
from typing import Literal

from ..helpers.detect import open_iterable
from ..types import Row

# Size thresholds in bytes.
SMALL_FILE_MAX = 1 * 1024 * 1024  # 1 MB
LARGE_FILE_MIN = 20 * 1024 * 1024  # 20 MB

SamplingTier = Literal["small", "medium", "large"]


def default_max_rows() -> int:
    """Resolve the default sampling row count from ``MAX_ROWS_SAMPLING``."""
    raw = os.environ.get("MAX_ROWS_SAMPLING")
    if raw:
        try:
            value = int(raw)
            if value > 0:
                return value
        except ValueError:
            pass
    return 50


@dataclass
class SamplingPlan:
    """Describes the chosen sampling strategy for an input."""

    tier: SamplingTier
    size_bytes: int | None
    head_rows: int
    random_rows: int
    include_rows: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "tier": self.tier,
            "size_bytes": self.size_bytes,
            "head_rows": self.head_rows,
            "random_rows": self.random_rows,
            "include_rows": self.include_rows,
        }


def choose_plan(size_bytes: int | None, max_rows: int | None = None) -> SamplingPlan:
    """Pick a :class:`SamplingPlan` based on input size in bytes.

    Args:
        size_bytes: Size of the input in bytes, or None when unknown (treated as small).
        max_rows: Override for the per-tier row count (defaults to ``MAX_ROWS_SAMPLING``).
    """
    n = max_rows if max_rows and max_rows > 0 else default_max_rows()

    if size_bytes is not None and size_bytes > LARGE_FILE_MIN:
        return SamplingPlan("large", size_bytes, head_rows=0, random_rows=0, include_rows=False)
    if size_bytes is not None and size_bytes > SMALL_FILE_MAX:
        # Medium: spec default is first 20 + 20 random; scale to N when N != 50.
        medium_n = min(n, 20) if n >= 20 else n
        return SamplingPlan("medium", size_bytes, head_rows=medium_n, random_rows=medium_n, include_rows=True)
    return SamplingPlan("small", size_bytes, head_rows=n, random_rows=0, include_rows=True)


def file_size(source: str | None) -> int | None:
    """Return the file size in bytes for a path, or None if not a real file."""
    if not source or not isinstance(source, str):
        return None
    try:
        return os.path.getsize(source)
    except OSError:
        return None


def sample_rows(
    iterable: collections.abc.Iterable[Row] | str,
    plan: SamplingPlan,
    *,
    seed: int | None = None,
) -> list[Row]:
    """Collect sample rows for an input according to a :class:`SamplingPlan`.

    Uses a single pass: keeps the first ``head_rows`` rows and reservoir-samples
    ``random_rows`` additional rows from the remainder. Returns an empty list when
    the plan excludes data rows (large tier).
    """
    if not plan.include_rows:
        return []

    source: collections.abc.Iterable[Row]
    opened = None
    if isinstance(iterable, str):
        opened = open_iterable(iterable)
        source = opened
    else:
        source = iterable

    rng = random.Random(seed)
    head: list[Row] = []
    reservoir: list[Row] = []
    seen_after_head = 0

    try:
        for row in source:
            if len(head) < plan.head_rows:
                head.append(row)
                continue
            if plan.random_rows <= 0:
                # Nothing more to collect once head is full.
                break
            seen_after_head += 1
            if len(reservoir) < plan.random_rows:
                reservoir.append(row)
            else:
                j = rng.randint(0, seen_after_head - 1)
                if j < plan.random_rows:
                    reservoir[j] = row
    finally:
        if opened is not None and hasattr(opened, "close"):
            opened.close()

    return head + reservoir
