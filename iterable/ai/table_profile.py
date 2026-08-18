"""Bounded multi-table profiling surface for documentation adapters.

This module is the streaming-safe public contract that advanced format
adapters must use. Callers enumerate tables, open one selected table as an
iterable, and run schema/sample/statistics/count under explicit budgets with
completeness flags. Full table materialization is never required.
"""

from __future__ import annotations

import time
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import Any

from iterable.ai import fileinfo, sampling
from iterable.ops import schema as schema_ops
from iterable.ops import stats as stats_ops
from iterable.types import Row


@dataclass(frozen=True)
class ProfileBudget:
    """Per-operation limits for one selected table."""

    max_sample_rows: int = 100
    max_schema_rows: int = 10_000
    max_stats_rows: int = 50_000
    max_count_rows: int | None = 1_000_000
    schema_seconds: float = 30.0
    sample_seconds: float = 30.0
    stats_seconds: float = 60.0
    count_seconds: float = 60.0


@dataclass
class CompletenessFlags:
    """Which profile facets completed within budget."""

    schema: bool = False
    sample: bool = False
    statistics: bool = False
    count: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass
class BoundedTableProfile:
    """Normalized profile result for one selected table/sheet."""

    table: str
    schema: dict[str, Any]
    samples: list[Row]
    statistics: dict[str, dict[str, Any]]
    record_count: int | None
    completeness: CompletenessFlags


def list_tables(source: str) -> list[str]:
    """Enumerate available tables/sheets without reading row payloads."""

    tables = fileinfo.list_tables(source)
    if not tables:
        return []
    return list(tables)


def open_selected_table(source: str, table: str) -> Any:
    """Open one named table/sheet as a streaming iterable."""

    return fileinfo.open_table(source, table)


def profile_selected_table(
    source: str,
    table: str,
    *,
    budget: ProfileBudget | None = None,
    size_bytes: int | None = None,
    include_statistics: bool = True,
    detect_constraints: bool = True,
) -> BoundedTableProfile:
    """Profile one table under budgets; never requires a full materialization."""

    limits = budget or ProfileBudget()
    completeness = CompletenessFlags()
    schema_info: dict[str, Any] = {}
    samples: list[Row] = []
    statistics: dict[str, dict[str, Any]] = {}
    record_count: int | None = None

    # Re-open per facet: many file iterables (SQLite, Excel) are single-pass.
    schema_info, completeness.schema = _bounded_schema(
        _open_facet(source, table),
        detect_constraints=detect_constraints,
        max_rows=limits.max_schema_rows,
        seconds=limits.schema_seconds,
        completeness=completeness,
    )
    samples, completeness.sample = _bounded_sample(
        _open_facet(source, table),
        size_bytes=size_bytes,
        max_rows=limits.max_sample_rows,
        seconds=limits.sample_seconds,
        completeness=completeness,
    )
    if include_statistics:
        statistics, completeness.statistics = _bounded_stats(
            _open_facet(source, table),
            max_rows=limits.max_stats_rows,
            seconds=limits.stats_seconds,
            completeness=completeness,
        )
    else:
        completeness.statistics = True
    record_count, completeness.count = _bounded_count(
        _open_facet(source, table),
        max_rows=limits.max_count_rows,
        seconds=limits.count_seconds,
        completeness=completeness,
    )

    return BoundedTableProfile(
        table=table,
        schema=schema_info,
        samples=samples,
        statistics=statistics,
        record_count=record_count,
        completeness=completeness,
    )


def _open_facet(source: str, table: str) -> Any:
    """Open one table and ensure the handle is closed after iteration when possible."""

    opened = open_selected_table(source, table)
    return _ClosingIterable(opened)


def _row_stream(source: Any, *, max_rows: int | None) -> Iterator[Row]:
    count = 0
    for row in source:
        yield row
        count += 1
        if max_rows is not None and count >= max_rows:
            return


def _bounded_schema(
    source: Any,
    *,
    detect_constraints: bool,
    max_rows: int,
    seconds: float,
    completeness: CompletenessFlags,
) -> tuple[dict[str, Any], bool]:
    started = time.monotonic()
    try:
        # Prefer pushdown when the iterable supports limited schema inference.
        result = schema_ops.infer(
            _DeadlineIterable(source, deadline=started + seconds, max_rows=max_rows),
            detect_constraints=detect_constraints,
            flatten_nested=True,
        )
        if time.monotonic() - started > seconds:
            completeness.warnings.append("schema inference hit time budget")
            return result or {}, False
        return result or {}, True
    except Exception as error:
        completeness.warnings.append(f"schema incomplete: {error.__class__.__name__}")
        return {}, False


def _bounded_sample(
    source: Any,
    *,
    size_bytes: int | None,
    max_rows: int,
    seconds: float,
    completeness: CompletenessFlags,
) -> tuple[list[Row], bool]:
    started = time.monotonic()
    try:
        plan = sampling.choose_plan(size_bytes, max_rows=max_rows)
        rows = sampling.sample_rows(
            _DeadlineIterable(source, deadline=started + seconds, max_rows=max_rows),
            plan,
        )
        if time.monotonic() - started > seconds:
            completeness.warnings.append("sampling hit time budget")
            return list(rows or []), False
        return list(rows or []), True
    except Exception as error:
        completeness.warnings.append(f"sample incomplete: {error.__class__.__name__}")
        return [], False


def _bounded_stats(
    source: Any,
    *,
    max_rows: int,
    seconds: float,
    completeness: CompletenessFlags,
) -> tuple[dict[str, dict[str, Any]], bool]:
    started = time.monotonic()
    try:
        result = stats_ops.compute(
            _DeadlineIterable(source, deadline=started + seconds, max_rows=max_rows),
            include_top_values=True,
            flatten_nested=True,
        )
        if time.monotonic() - started > seconds:
            completeness.warnings.append("statistics hit time budget")
            return result or {}, False
        return result or {}, True
    except Exception as error:
        completeness.warnings.append(f"statistics incomplete: {error.__class__.__name__}")
        return {}, False


def _bounded_count(
    source: Any,
    *,
    max_rows: int | None,
    seconds: float,
    completeness: CompletenessFlags,
) -> tuple[int | None, bool]:
    started = time.monotonic()
    try:
        total = 0
        for _ in _DeadlineIterable(source, deadline=started + seconds, max_rows=max_rows):
            total += 1
        if time.monotonic() - started > seconds:
            completeness.warnings.append("count hit time budget")
            return total, False
        if max_rows is not None and total >= max_rows:
            completeness.warnings.append("count hit row budget")
            return total, False
        return total, True
    except Exception as error:
        completeness.warnings.append(f"count incomplete: {error.__class__.__name__}")
        return None, False


class _ClosingIterable:
    """Iterate a source once, then close it if it exposes ``close()``."""

    def __init__(self, source: Any) -> None:
        self._source = source

    def __iter__(self) -> Iterator[Row]:
        try:
            yield from self._source
        finally:
            close = getattr(self._source, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass


class _DeadlineIterable:
    """Wrap an iterable with wall-clock and row ceilings."""

    def __init__(
        self,
        source: Iterable[Row],
        *,
        deadline: float,
        max_rows: int | None,
    ) -> None:
        self._source = source
        self._deadline = deadline
        self._max_rows = max_rows

    def __iter__(self) -> Iterator[Row]:
        count = 0
        for row in self._source:
            if time.monotonic() >= self._deadline:
                return
            yield row
            count += 1
            if self._max_rows is not None and count >= self._max_rows:
                return


__all__ = [
    "BoundedTableProfile",
    "CompletenessFlags",
    "ProfileBudget",
    "list_tables",
    "open_selected_table",
    "profile_selected_table",
]
