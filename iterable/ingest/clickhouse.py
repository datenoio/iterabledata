"""
ClickHouse database ingestor.
"""

from __future__ import annotations

import collections.abc
import itertools
import time
from collections.abc import Callable
from typing import Any

try:
    import clickhouse_connect
except ImportError:
    clickhouse_connect = None

from ..types import Row
from ._sql_base import run_batched_ingest
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
    Ingest data into ClickHouse database.

    Args:
        iterable: An iterable of row dictionaries
        db_url: ClickHouse connection URL (clickhouse://user:pass@host:port/dbname)
        table: Table name (optionally database-qualified as "database.table")
        mode: Ingestion mode - only "insert" is supported. ClickHouse has no row-level
            UPDATE, so mode="upsert" raises ValueError.
        upsert_key: Field name(s) for upsert matching (unsupported; must stay None)
        batch: Batch size for bulk inserts
        create_table: Whether to auto-create the table. Columns are created as
            Nullable(String) under ``ENGINE = MergeTree ORDER BY tuple()``.
        progress: Optional progress callback

    Returns:
        IngestionResult with statistics
    """
    if mode == "upsert":
        raise ValueError(
            "ClickHouse ingestion does not support mode='upsert': ClickHouse has no row-level UPDATE. "
            "Use mode='insert'."
        )
    if clickhouse_connect is None:
        raise ImportError(
            "clickhouse-connect is required for ClickHouse ingestion. Install with: pip install clickhouse-connect"
        )

    start_time = time.time()
    rows_processed = 0
    rows_inserted = 0
    errors: list[str] = []

    try:
        client = clickhouse_connect.get_client(url=db_url)

        iterator = iter(iterable)
        first_row = next(iterator, None)
        if first_row is None:
            client.close()
            return IngestionResult(elapsed_seconds=time.time() - start_time)

        if create_table:
            _create_text_table(client, table, first_row)

        rows_processed, rows_inserted = run_batched_ingest(
            itertools.chain([first_row], iterator),
            batch=batch,
            progress=progress,
            insert_batch=lambda rows: _insert_batch(client, table, rows),
        )

        client.close()

    except Exception as e:
        errors.append(str(e))

    return IngestionResult(
        rows_processed=rows_processed,
        rows_inserted=rows_inserted,
        errors=errors,
        elapsed_seconds=time.time() - start_time,
    )


def _create_text_table(client: Any, table: str, first_row: Row) -> None:
    """Create a table with Nullable(String) columns inferred from the first row's keys.

    ClickHouse requires an ENGINE clause; MergeTree with ``ORDER BY tuple()`` is the
    simplest general-purpose choice (no sorting key).
    """
    columns = quote_columns(list(first_row.keys()), quote_char="`")
    columns_def = ", ".join(f"{col} Nullable(String)" for col in columns)
    quoted_table = quote_table_name(table, quote_char="`")
    # Identifiers quoted via quote_table_name()/quote_columns(); no row values in this statement.
    create_query = f"CREATE TABLE IF NOT EXISTS {quoted_table} ({columns_def}) ENGINE = MergeTree ORDER BY tuple()"  # nosec B608
    client.command(create_query)


def _insert_batch(client: Any, table: str, rows: list[Row]) -> None:
    """Insert a batch of rows into ClickHouse."""
    if not rows:
        return

    columns = list(rows[0].keys())
    quoted_table = quote_table_name(table, quote_char="`")
    quoted_columns = quote_columns(columns, quote_char="`")
    values = [[row.get(col) for col in columns] for row in rows]
    client.insert(quoted_table, values, column_names=quoted_columns)
