"""
SQLite database driver.

Provides read-only access to SQLite databases as iterable data sources.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from typing import Any

from ..types import Row
from .base import DBDriver


class SQLiteDriver(DBDriver):
    """SQLite database driver.

    Supports batch processing for memory efficiency.
    Uses sqlite3 (standard library).
    """

    def __init__(self, source: str | Any, **kwargs: Any) -> None:
        """Initialize SQLite driver.

        Args:
            source: SQLite database file path (e.g., 'database.db') or ':memory:' or existing sqlite3.Connection
            **kwargs: Additional parameters:
                - query: SQL query string or table name
                - batch_size: Number of rows per batch (default: 10000)
                - columns: List of column names for projection
                - filter: WHERE clause fragment (e.g., "active = 1")
                - connect_args: Additional arguments for sqlite3.connect()
                    (e.g., timeout, check_same_thread, isolation_level)
        """
        super().__init__(source, **kwargs)
        self._cursor: Any = None
        self._column_names: list[str] | None = None

    def connect(self) -> None:
        """Establish SQLite connection.

        Raises:
            ConnectionError: If connection fails
        """
        # If source is already a connection object, use it
        if isinstance(self.source, sqlite3.Connection):
            self.conn = self.source
            self._connected = True
            return

        # Parse connection string
        if not isinstance(self.source, str):
            raise ValueError(
                f"SQLite source must be a file path, ':memory:', or sqlite3.Connection object, got {type(self.source)}"
            )

        # Extract connection arguments
        connect_args = self.kwargs.get("connect_args", {})

        try:
            # SQLite connection
            # Default to read-only mode for safety (if file exists)
            if self.source != ":memory:":
                # Try to open in read-only mode first
                try:
                    import os

                    if os.path.exists(self.source):
                        # Open in read-only mode
                        self.conn = sqlite3.connect(f"file:{self.source}?mode=ro", uri=True, **connect_args)
                    else:
                        # File doesn't exist - open normally (will create empty DB)
                        # But we're read-only, so this shouldn't happen in practice
                        self.conn = sqlite3.connect(self.source, **connect_args)
                except Exception:
                    # Fallback to normal connection if URI mode fails
                    self.conn = sqlite3.connect(self.source, **connect_args)
            else:
                # In-memory database
                self.conn = sqlite3.connect(self.source, **connect_args)

            # Enable row factory for dict-like access (we'll convert manually)
            self.conn.row_factory = sqlite3.Row

            self._connected = True

        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to SQLite: {e}") from e

    def _build_query(self) -> str:
        """Build SQL query from parameters.

        Returns:
            SQL query string
        """
        query = self.kwargs.get("query")
        if not query:
            raise ValueError("'query' parameter is required for SQLite driver")

        # If query looks like a table name (no SQL keywords), build SELECT query
        query_upper = query.strip().upper()
        sql_keywords = {"SELECT", "WITH", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"}

        if not any(query_upper.startswith(kw) for kw in sql_keywords):
            # Treat as table name - build SELECT query
            table = query.strip()

            # Build column list
            columns = self.kwargs.get("columns")
            if columns:
                col_list = ", ".join([self._quote_identifier(col) for col in columns])
            else:
                col_list = "*"

            # Build table reference
            table_ref = self._quote_identifier(table)

            # Build WHERE clause
            filter_clause = self.kwargs.get("filter")
            where_clause = f" WHERE {filter_clause}" if filter_clause else ""

            query = f"SELECT {col_list} FROM {table_ref}{where_clause}"

        return query

    def _quote_identifier(self, identifier: str) -> str:
        """Quote SQLite identifier.

        Args:
            identifier: Identifier to quote

        Returns:
            Quoted identifier
        """
        # SQLite uses double quotes for identifiers
        # Escape double quotes by doubling them
        escaped = identifier.replace('"', '""')
        return f'"{escaped}"'

    def iterate(self) -> Iterator[Row]:
        """Return iterator of dict rows from SQLite query.

        Yields:
            dict: Database row as dictionary

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected or self.conn is None:
            raise RuntimeError("Not connected to database. Call connect() first.")

        # Build query
        try:
            query = self._build_query()
        except Exception as e:
            self._handle_error(e, "building query")
            if self._on_error == "raise":
                raise
            return

        # Get batch size
        batch_size = self.kwargs.get("batch_size", 10000)

        # Start metrics
        self._start_metrics()

        try:
            # Create cursor
            self._cursor = self.conn.cursor()

            # Execute query
            try:
                self._cursor.execute(query)
            except Exception as e:
                self._handle_error(e, f"executing query: {query[:100]}")
                if self._on_error == "raise":
                    raise
                return

            # Get column names
            if self._cursor.description:
                self._column_names = [desc[0] for desc in self._cursor.description]
            else:
                # No columns (e.g., INSERT, UPDATE without RETURNING)
                self._column_names = []

            # Iterate over results using fetchmany for batch processing
            while True:
                try:
                    rows = self._cursor.fetchmany(batch_size)
                    if not rows:
                        break

                    for row in rows:
                        if self._column_names:
                            # Convert row to dict
                            # sqlite3.Row objects can be converted to dict
                            if isinstance(row, sqlite3.Row):
                                yield dict(row)
                            else:
                                yield dict(zip(self._column_names, row, strict=False))
                        else:
                            # No column names - return empty dict
                            yield {}

                        self._update_metrics(rows_read=1)
                except Exception as e:
                    self._handle_error(e, "fetching rows")
                    if self._on_error == "raise":
                        raise
                    break

        finally:
            # Clean up cursor
            if self._cursor is not None:
                try:
                    self._cursor.close()
                except Exception:
                    pass
                self._cursor = None

    def close(self) -> None:
        """Close SQLite connection and clean up resources."""
        # Close cursor first
        if self._cursor is not None:
            try:
                self._cursor.close()
            except Exception:
                pass
            self._cursor = None

        # Close connection
        super().close()

    @staticmethod
    def list_tables(
        connection_string: str,
        schema: str | None = None,
        **connect_args: Any,
    ) -> list[dict[str, Any]]:
        """List tables in SQLite database.

        Args:
            connection_string: SQLite database file path or ':memory:'
            schema: Not used for SQLite (kept for API consistency)
            **connect_args: Additional connection arguments

        Returns:
            List of dicts with keys: schema, table, row_count (estimate)

        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Parse connection string similar to connect()
            if connection_string == ":memory:":
                conn = sqlite3.connect(connection_string, **connect_args)
            else:
                try:
                    import os

                    if os.path.exists(connection_string):
                        conn = sqlite3.connect(f"file:{connection_string}?mode=ro", uri=True, **connect_args)
                    else:
                        conn = sqlite3.connect(connection_string, **connect_args)
                except Exception:
                    conn = sqlite3.connect(connection_string, **connect_args)

            conn.row_factory = sqlite3.Row

            # sqlite3.Cursor does not support the context manager protocol,
            # so manage it explicitly.
            cur = conn.cursor()
            try:
                # Query sqlite_master for tables
                query = """
                    SELECT 
                        'main' as schema,
                        name as table_name,
                        (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as row_count
                    FROM sqlite_master m
                    WHERE type = 'table'
                        AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """
                cur.execute(query)

                results = []
                for row in cur.fetchall():
                    # Get actual row count for each table
                    table_name = row[1]
                    try:
                        count_cur = conn.cursor()
                        # Quote identifier manually
                        escaped = table_name.replace('"', '""')
                        quoted_name = f'"{escaped}"'
                        count_cur.execute(f"SELECT COUNT(*) FROM {quoted_name}")
                        row_count = count_cur.fetchone()[0]
                        count_cur.close()
                    except Exception:
                        row_count = None

                    results.append(
                        {
                            "schema": row[0],
                            "table": table_name,
                            "row_count": row_count,
                        }
                    )

                return results
            finally:
                cur.close()
                conn.close()

        except Exception as e:
            raise ConnectionError(f"Failed to list tables from SQLite: {e}") from e
