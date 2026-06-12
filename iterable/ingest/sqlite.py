"""
SQLite database ingestor.
"""

from __future__ import annotations

import collections.abc
import sqlite3
import time
from collections.abc import Callable
from typing import Any

from ..types import Row
from .core import IngestionResult
from .identifiers import quote_columns, quote_table_name


def ingest(
    iterable: collections.abc.Iterable[Row],
    db_url: str,
    table: str,
    mode: str = "insert",
    upsert_key: str | list[str] | None = None,
    batch: int = 5000,
    create_table: bool = False,
    progress: Callable[[dict[str, Any]], None] | None = None,
) -> IngestionResult:
    """
    Ingest data into SQLite database.

    Args:
        iterable: An iterable of row dictionaries
        db_url: SQLite database file path
        table: Table name
        mode: Ingestion mode - "insert" or "upsert"
        upsert_key: Field name(s) for upsert matching
        batch: Batch size for bulk inserts
        create_table: Whether to auto-create table
        progress: Optional progress callback

    Returns:
        IngestionResult with statistics
    """
    start_time = time.time()
    rows_processed = 0
    rows_inserted = 0
    rows_updated = 0
    errors: list[str] = []

    try:
        conn = sqlite3.connect(db_url)
        cursor = conn.cursor()

        # Get first row to determine schema
        iterator = iter(iterable)
        first_row = next(iterator, None)
        if first_row is None:
            return IngestionResult(elapsed_seconds=time.time() - start_time)

        # Create table if needed
        if create_table:
            columns = quote_columns(list(first_row.keys()))
            columns_def = ", ".join([f"{col} TEXT" for col in columns])
            create_query = f"CREATE TABLE IF NOT EXISTS {quote_table_name(table)} ({columns_def})"
            cursor.execute(create_query)
            conn.commit()

        # Prepare batch
        batch_rows: list[Row] = [first_row]
        rows_processed = 1

        # Process remaining rows
        for row in iterator:
            batch_rows.append(row)
            rows_processed += 1

            if len(batch_rows) >= batch:
                _insert_batch(cursor, conn, table, batch_rows, mode, upsert_key)
                rows_inserted += len(batch_rows)
                batch_rows = []

                if progress:
                    progress({"rows_processed": rows_processed, "rows_inserted": rows_inserted})

        # Insert remaining batch
        if batch_rows:
            _insert_batch(cursor, conn, table, batch_rows, mode, upsert_key)
            rows_inserted += len(batch_rows)

        conn.commit()
        conn.close()

    except Exception as e:
        errors.append(str(e))

    return IngestionResult(
        rows_processed=rows_processed,
        rows_inserted=rows_inserted,
        rows_updated=rows_updated,
        errors=errors,
        elapsed_seconds=time.time() - start_time,
    )


def _insert_batch(
    cursor: sqlite3.Cursor,
    conn: sqlite3.Connection,
    table: str,
    rows: list[Row],
    mode: str,
    upsert_key: str | list[str] | None,
):
    """Insert a batch of rows into SQLite."""
    if not rows:
        return

    columns = list(rows[0].keys())
    quoted_table = quote_table_name(table)
    placeholders = ", ".join(["?" for _ in columns])
    columns_str = ", ".join(quote_columns(columns))

    if mode == "upsert" and upsert_key:
        # SQLite UPSERT (INSERT OR REPLACE)
        if isinstance(upsert_key, str):
            upsert_key = [upsert_key]
        # Build INSERT OR REPLACE query
        query = f"INSERT OR REPLACE INTO {quoted_table} ({columns_str}) VALUES ({placeholders})"
    else:
        # Simple INSERT
        query = f"INSERT INTO {quoted_table} ({columns_str}) VALUES ({placeholders})"

    values = [[row.get(col) for col in columns] for row in rows]
    cursor.executemany(query, values)
    conn.commit()
