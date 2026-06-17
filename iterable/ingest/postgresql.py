"""
PostgreSQL database ingestor.
"""

from __future__ import annotations

import collections.abc
import itertools
import time
from collections.abc import Callable
from typing import Any

try:
    import psycopg
    from psycopg import sql
    from psycopg.pool import ConnectionPool
except ImportError:
    psycopg = None
    sql = None
    ConnectionPool = None

from ..types import Row
from ._sql_base import create_text_table, run_batched_ingest
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
    Ingest data into PostgreSQL database.

    Args:
        iterable: An iterable of row dictionaries
        db_url: PostgreSQL connection URL
        table: Table name
        mode: Ingestion mode - "insert" or "upsert"
        upsert_key: Field name(s) for upsert matching
        batch: Batch size for bulk inserts
        create_table: Whether to auto-create table
        progress: Optional progress callback

    Returns:
        IngestionResult with statistics
    """
    if psycopg is None:
        raise ImportError("psycopg is required for PostgreSQL ingestion. Install with: pip install 'psycopg[binary]'")

    start_time = time.time()
    rows_processed = 0
    rows_inserted = 0
    rows_updated = 0
    errors: list[str] = []

    try:
        conn = psycopg.connect(db_url)

        iterator = iter(iterable)
        first_row = next(iterator, None)
        if first_row is None:
            conn.close()
            return IngestionResult(elapsed_seconds=time.time() - start_time)

        if create_table:
            create_text_table(conn.execute, conn.commit, table, first_row)

        rows_processed, rows_inserted = run_batched_ingest(
            itertools.chain([first_row], iterator),
            batch=batch,
            progress=progress,
            insert_batch=lambda rows: _insert_batch(conn, table, rows, mode, upsert_key),
        )

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
    conn: Any,
    table: str,
    rows: list[Row],
    mode: str,
    upsert_key: str | list[str] | None,
):
    """Insert a batch of rows into PostgreSQL."""
    if not rows:
        return

    columns = list(rows[0].keys())
    quoted_table = quote_table_name(table)
    quoted_columns = quote_columns(columns)
    columns_str = ", ".join(quoted_columns)
    placeholders = ", ".join(["%s" for _ in columns])

    if mode == "upsert" and upsert_key:
        # PostgreSQL UPSERT (ON CONFLICT)
        if isinstance(upsert_key, str):
            upsert_key = [upsert_key]
        update_clause = ", ".join(
            [
                f"{qcol} = EXCLUDED.{qcol}"
                for col, qcol in zip(columns, quoted_columns, strict=True)
                if col not in upsert_key
            ]
        )
        conflict_clause = ", ".join(quote_columns(list(upsert_key)))
        query = f"""INSERT INTO {quoted_table} ({columns_str}) 
                    VALUES ({placeholders})
                    ON CONFLICT ({conflict_clause}) 
                    DO UPDATE SET {update_clause}"""
    else:
        query = f"INSERT INTO {quoted_table} ({columns_str}) VALUES ({placeholders})"

    values = [[row.get(col) for col in columns] for row in rows]
    conn.executemany(query, values)
    conn.commit()
