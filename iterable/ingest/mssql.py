"""
Microsoft SQL Server database ingestor.
"""

from __future__ import annotations

import collections.abc
import itertools
import time
from collections.abc import Callable
from typing import Any

try:
    import pyodbc
except ImportError:
    pyodbc = None

from ..db.mssql import _build_connection_string
from ..types import Row
from ._sql_base import run_batched_ingest
from .core import IngestionResult
from .identifiers import validate_identifier


def _quote_identifier(name: str, kind: str = "identifier") -> str:
    """Validate, escape and quote a single T-SQL identifier with square brackets.

    Mirrors the bracket quoting used by the MSSQL read driver: embedded closing
    brackets are escaped by doubling them.
    """
    validate_identifier(name, kind=kind)
    escaped = name.replace("]", "]]")
    return f"[{escaped}]"


def _quote_table_name(table: str) -> str:
    """Validate and quote a table name, allowing an optional schema qualifier."""
    parts = table.split(".") if "." in table and table.count(".") == 1 else [table]
    return ".".join(_quote_identifier(part, kind="table name") for part in parts)


def _quote_columns(columns: list[str]) -> list[str]:
    """Validate and quote a list of column names."""
    return [_quote_identifier(col, kind="column name") for col in columns]


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
    Ingest data into Microsoft SQL Server database.

    Args:
        iterable: An iterable of row dictionaries
        db_url: SQL Server connection URL (mssql://user:pass@host:port/dbname?driver=...),
            a mssql+pyodbc:// or odbc:// URL, a DSN, or a full pyodbc connection string
        table: Table name (optionally schema-qualified as "schema.table", default schema is dbo)
        mode: Ingestion mode - only "insert" is supported; MERGE-based upsert is not
            implemented, so mode="upsert" raises ValueError.
        upsert_key: Field name(s) for upsert matching (unsupported; must stay None)
        batch: Batch size for bulk inserts
        create_table: Whether to auto-create the table (NVARCHAR(MAX) columns)
        progress: Optional progress callback

    Returns:
        IngestionResult with statistics
    """
    if mode == "upsert":
        raise ValueError(
            "MSSQL ingestion does not support mode='upsert' (MERGE-based upsert is not implemented). Use mode='insert'."
        )
    if pyodbc is None:
        raise ImportError("pyodbc is required for MSSQL ingestion. Install with: pip install pyodbc")

    start_time = time.time()
    rows_processed = 0
    rows_inserted = 0
    rows_updated = 0
    errors: list[str] = []

    try:
        conn = pyodbc.connect(_build_connection_string(db_url, {}))
        cursor = conn.cursor()

        iterator = iter(iterable)
        first_row = next(iterator, None)
        if first_row is None:
            cursor.close()
            conn.close()
            return IngestionResult(elapsed_seconds=time.time() - start_time)

        if create_table:
            _create_text_table(cursor, conn, table, first_row)

        rows_processed, rows_inserted = run_batched_ingest(
            itertools.chain([first_row], iterator),
            batch=batch,
            progress=progress,
            insert_batch=lambda rows: _insert_batch(cursor, conn, table, rows),
        )

        conn.commit()
        cursor.close()
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


def _create_text_table(cursor: Any, conn: Any, table: str, first_row: Row) -> None:
    """Create a table with NVARCHAR(MAX) columns inferred from the first row's keys.

    T-SQL has no ``CREATE TABLE IF NOT EXISTS``, so guard creation with an
    ``OBJECT_ID`` lookup instead.
    """
    columns = _quote_columns(list(first_row.keys()))
    columns_def = ", ".join(f"{col} NVARCHAR(MAX)" for col in columns)
    quoted_table = _quote_table_name(table)
    # OBJECT_ID() needs the raw name as a string literal; escape single quotes by doubling.
    literal = table.replace("'", "''")
    # Identifiers quoted via _quote_table_name()/_quote_columns(); literal is quote-escaped
    # and validated against control characters by validate_identifier().
    create_query = f"IF OBJECT_ID(N'{literal}', N'U') IS NULL CREATE TABLE {quoted_table} ({columns_def})"  # nosec B608
    cursor.execute(create_query)
    conn.commit()


def _insert_batch(cursor: Any, conn: Any, table: str, rows: list[Row]) -> None:
    """Insert a batch of rows into SQL Server."""
    if not rows:
        return

    columns = list(rows[0].keys())
    quoted_table = _quote_table_name(table)
    columns_str = ", ".join(_quote_columns(columns))
    placeholders = ", ".join(["?" for _ in columns])
    # Identifiers quoted via _quote_table_name()/_quote_columns(); row values are bound parameters.
    query = f"INSERT INTO {quoted_table} ({columns_str}) VALUES ({placeholders})"  # nosec B608

    values = [[row.get(col) for col in columns] for row in rows]
    cursor.executemany(query, values)
    conn.commit()
