"""
Core database ingestion engine.

Provides unified API for ingesting data into various databases.
"""

from __future__ import annotations

import collections.abc
from collections.abc import Callable
from typing import Any

from ..helpers.detect import open_iterable
from ..types import Row


class IngestionResult:
    """Result of database ingestion operation."""

    def __init__(
        self,
        rows_processed: int = 0,
        rows_inserted: int = 0,
        rows_updated: int = 0,
        errors: list[str] = None,
        elapsed_seconds: float = 0.0,
    ):
        self.rows_processed = rows_processed
        self.rows_inserted = rows_inserted
        self.rows_updated = rows_updated
        self.errors = errors or []
        self.elapsed_seconds = elapsed_seconds


def to_db(
    iterable: collections.abc.Iterable[Row],
    db_url: str,
    table: str,
    dbtype: str,
    mode: str = "insert",
    upsert_key: str | list[str] | None = None,
    batch: int = 5000,
    create_table: bool = False,
    totals: bool = False,
    progress: Callable[[dict[str, Any]], None] | None = None,
) -> IngestionResult:
    """
    Ingest data from an iterable into a database.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        db_url: Database connection URL or file path
        table: Table/collection name
        dbtype: Database type - "postgresql", "mongodb", "duckdb", "mysql", "sqlite", "elasticsearch"
        mode: Ingestion mode - "insert" or "upsert" (default: "insert")
        upsert_key: Field name(s) to use for upsert matching (required if mode="upsert")
        batch: Batch size for bulk operations (default: 5000)
        create_table: Whether to auto-create table/collection if it doesn't exist (default: False)
        totals: Whether to return detailed statistics (default: False)
        progress: Optional progress callback function

    Returns:
        IngestionResult object with statistics

    Example:
        >>> from iterable import ingest
        >>> result = ingest.to_db(
        ...     "data.csv",
        ...     db_url="postgresql://user:pass@localhost:5432/mydb",
        ...     table="users",
        ...     dbtype="postgresql",
        ...     mode="upsert",
        ...     upsert_key="id"
        ... )
        >>> print(f"Inserted: {result.rows_inserted}")
    """
    if isinstance(iterable, str):
        iterable = open_iterable(iterable)

    # Route to appropriate ingestor
    if dbtype == "postgresql":
        from . import postgresql

        return postgresql.ingest(iterable, db_url, table, mode, upsert_key, batch, create_table, progress)
    elif dbtype == "sqlite":
        from . import sqlite

        return sqlite.ingest(iterable, db_url, table, mode, upsert_key, batch, create_table, progress)
    elif dbtype == "duckdb":
        from . import duckdb

        return duckdb.ingest(iterable, db_url, table, mode, upsert_key, batch, create_table, progress)
    elif dbtype == "mongodb":
        from . import mongodb

        return mongodb.ingest(iterable, db_url, table, mode, upsert_key, batch, create_table, progress)
    elif dbtype == "mysql":
        from . import mysql

        return mysql.ingest(iterable, db_url, table, mode, upsert_key, batch, create_table, progress)
    elif dbtype == "elasticsearch":
        from . import elasticsearch

        return elasticsearch.ingest(iterable, db_url, table, mode, upsert_key, batch, create_table, progress)
    else:
        raise ValueError(f"Unsupported database type: {dbtype}")
