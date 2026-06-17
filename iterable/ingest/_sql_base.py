"""Shared helpers for SQL database ingest backends."""

from __future__ import annotations

import collections.abc
from collections.abc import Callable
from typing import Any

from ..types import Row
from .identifiers import quote_columns, quote_table_name


def create_text_table(
    execute: Callable[[str], Any],
    commit: Callable[[], Any],
    table: str,
    first_row: Row,
    *,
    quote_char: str = '"',
) -> None:
    """Create a table with TEXT columns inferred from the first row's keys."""
    columns = quote_columns(list(first_row.keys()), quote_char=quote_char)
    columns_def = ", ".join(f"{col} TEXT" for col in columns)
    create_query = f"CREATE TABLE IF NOT EXISTS {quote_table_name(table, quote_char=quote_char)} ({columns_def})"
    execute(create_query)
    commit()


def run_batched_ingest(
    iterable: collections.abc.Iterable[Row],
    *,
    batch: int,
    insert_batch: Callable[[list[Row]], None],
    progress: Callable[[dict[str, Any]], None] | None = None,
) -> tuple[int, int]:
    """Insert rows in batches. Returns ``(rows_processed, rows_inserted)``."""
    rows_processed = 0
    rows_inserted = 0
    batch_rows: list[Row] = []

    for row in iterable:
        batch_rows.append(row)
        rows_processed += 1

        if len(batch_rows) >= batch:
            insert_batch(batch_rows)
            rows_inserted += len(batch_rows)
            batch_rows = []
            if progress:
                progress({"rows_processed": rows_processed, "rows_inserted": rows_inserted})

    if batch_rows:
        insert_batch(batch_rows)
        rows_inserted += len(batch_rows)

    return rows_processed, rows_inserted
