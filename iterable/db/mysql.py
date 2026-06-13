"""
MySQL/MariaDB database driver.

Provides read-only access to MySQL/MariaDB databases as iterable data sources.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..types import Row
from .base import DBDriver

# Imported at module level (guarded) so the optional dependency stays optional
# while remaining patchable as ``iterable.db.mysql.pymysql`` in tests.
try:
    import pymysql
except ImportError:  # pragma: no cover - exercised when dependency is absent
    pymysql = None


class MySQLDriver(DBDriver):
    """MySQL/MariaDB database driver.

    Supports streaming queries using server-side cursors (SSCursor) for memory efficiency.
    Uses pymysql (pure Python MySQL client).
    """

    def __init__(self, source: str | Any, **kwargs: Any) -> None:
        """Initialize MySQL driver.

        Args:
            source: MySQL connection string (mysql://...) or existing pymysql connection
            **kwargs: Additional parameters:
                - query: SQL query string or table name
                - batch_size: Number of rows per batch (default: 10000)
                - schema: Database/schema name for table references
                - columns: List of column names for projection
                - filter: WHERE clause fragment (e.g., "active = TRUE")
                - server_side_cursor: Use server-side cursor (default: True)
                - connect_args: Additional arguments for pymysql.connect()
        """
        super().__init__(source, **kwargs)
        self._cursor: Any = None
        self._column_names: list[str] | None = None

    def connect(self) -> None:
        """Establish MySQL connection.

        Raises:
            ImportError: If pymysql is not installed
            ConnectionError: If connection fails
        """
        # If source is already a connection object, use it (no driver import needed)
        if hasattr(self.source, "cursor") and hasattr(self.source, "close"):
            self.conn = self.source
            self._connected = True
            return

        # Validate source type before requiring the driver dependency
        if not isinstance(self.source, str):
            raise ValueError(f"MySQL source must be a connection string or connection object, got {type(self.source)}")

        if pymysql is None:
            raise ImportError("pymysql is required for MySQL support. Install it with: pip install pymysql")

        # Extract connection arguments
        connect_args = self.kwargs.get("connect_args", {})

        try:
            # Parse connection string if it's a URL
            if self.source.startswith("mysql://") or self.source.startswith("mysql+pymysql://"):
                # Parse URL format: mysql://user:pass@host:port/database
                from urllib.parse import urlparse

                parsed = urlparse(self.source)
                if parsed.username:
                    connect_args["user"] = parsed.username
                if parsed.password:
                    connect_args["password"] = parsed.password
                if parsed.hostname:
                    connect_args["host"] = parsed.hostname
                if parsed.port:
                    connect_args["port"] = parsed.port
                if parsed.path:
                    db_name = parsed.path.lstrip("/")
                    if db_name:
                        connect_args["database"] = db_name
            else:
                # Assume it's a DSN string or use as host
                # For DSN strings, pymysql.connect() will parse them
                # For simple host strings, use as host
                if "://" not in self.source:
                    connect_args["host"] = self.source

            self.conn = pymysql.connect(**connect_args)
            self._connected = True

        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to MySQL: {e}") from e

    def _build_query(self) -> str:
        """Build SQL query from parameters.

        Returns:
            SQL query string
        """
        query = self.kwargs.get("query")
        if not query:
            raise ValueError("'query' parameter is required for MySQL driver")

        # If query looks like a table name (no SQL keywords), build SELECT query
        query_upper = query.strip().upper()
        sql_keywords = {"SELECT", "WITH", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"}

        if not any(query_upper.startswith(kw) for kw in sql_keywords):
            # Treat as table name - build SELECT query
            schema = self.kwargs.get("schema")
            table = query.strip()

            # Build column list
            columns = self.kwargs.get("columns")
            if columns:
                col_list = ", ".join([self._quote_identifier(col) for col in columns])
            else:
                col_list = "*"

            # Build table reference
            if schema:
                table_ref = f"{self._quote_identifier(schema)}.{self._quote_identifier(table)}"
            else:
                table_ref = self._quote_identifier(table)

            # Build WHERE clause
            filter_clause = self.kwargs.get("filter")
            where_clause = f" WHERE {filter_clause}" if filter_clause else ""

            query = f"SELECT {col_list} FROM {table_ref}{where_clause}"

        return query

    def _quote_identifier(self, identifier: str) -> str:
        """Quote MySQL identifier.

        Args:
            identifier: Identifier to quote

        Returns:
            Quoted identifier
        """
        # MySQL uses backticks for identifiers
        # Escape backticks by doubling them
        escaped = identifier.replace("`", "``")
        return f"`{escaped}`"

    def iterate(self) -> Iterator[Row]:
        """Return iterator of dict rows from MySQL query.

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
        server_side_cursor = self.kwargs.get("server_side_cursor", True)

        # Start metrics
        self._start_metrics()

        try:
            # Create cursor
            if server_side_cursor:
                # Use SSCursor (server-side cursor) for streaming
                self._cursor = self.conn.cursor(pymysql.cursors.SSCursor)
            else:
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

            # Iterate over results
            if server_side_cursor:
                # For server-side cursors, fetch in batches
                while True:
                    try:
                        rows = self._cursor.fetchmany(batch_size)
                        if not rows:
                            break

                        for row in rows:
                            if self._column_names:
                                yield dict(zip(self._column_names, row, strict=False))
                            else:
                                # No column names - return as tuple or empty dict
                                yield {}

                            self._update_metrics(rows_read=1)
                    except Exception as e:
                        self._handle_error(e, "fetching rows")
                        if self._on_error == "raise":
                            raise
                        break
            else:
                # For regular cursors, iterate directly
                try:
                    for row in self._cursor:
                        if self._column_names:
                            yield dict(zip(self._column_names, row, strict=False))
                        else:
                            yield {}

                        self._update_metrics(rows_read=1)
                except Exception as e:
                    self._handle_error(e, "iterating rows")
                    if self._on_error == "raise":
                        raise

        finally:
            # Clean up cursor
            if self._cursor is not None:
                try:
                    self._cursor.close()
                except Exception:
                    pass
                self._cursor = None

    def close(self) -> None:
        """Close MySQL connection and clean up resources."""
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
        """List tables in MySQL database.

        Args:
            connection_string: MySQL connection string
            schema: Optional database/schema name (default: current database)
            **connect_args: Additional connection arguments

        Returns:
            List of dicts with keys: schema, table, row_count (estimate)

        Raises:
            ImportError: If pymysql is not installed
            ConnectionError: If connection fails
        """
        if pymysql is None:
            raise ImportError("pymysql is required for MySQL support. Install it with: pip install pymysql")

        try:
            # Parse connection string similar to connect()
            parsed_args = connect_args.copy()
            if connection_string.startswith("mysql://") or connection_string.startswith("mysql+pymysql://"):
                from urllib.parse import urlparse

                parsed = urlparse(connection_string)
                if parsed.username:
                    parsed_args["user"] = parsed.username
                if parsed.password:
                    parsed_args["password"] = parsed.password
                if parsed.hostname:
                    parsed_args["host"] = parsed.hostname
                if parsed.port:
                    parsed_args["port"] = parsed.port
                if parsed.path:
                    db_name = parsed.path.lstrip("/")
                    if db_name:
                        parsed_args["database"] = db_name
            elif "://" not in connection_string:
                parsed_args["host"] = connection_string

            conn = pymysql.connect(**parsed_args)
            with conn.cursor() as cur:
                # Query INFORMATION_SCHEMA
                if schema:
                    query = """
                        SELECT 
                            table_schema,
                            table_name,
                            table_rows as row_count
                        FROM information_schema.tables
                        WHERE table_schema = %s
                            AND table_type = 'BASE TABLE'
                        ORDER BY table_schema, table_name
                    """
                    cur.execute(query, (schema,))
                else:
                    # Use current database
                    cur.execute("SELECT DATABASE()")
                    current_db = cur.fetchone()[0]
                    if current_db:
                        query = """
                            SELECT 
                                table_schema,
                                table_name,
                                table_rows as row_count
                            FROM information_schema.tables
                            WHERE table_schema = %s
                                AND table_type = 'BASE TABLE'
                            ORDER BY table_schema, table_name
                        """
                        cur.execute(query, (current_db,))
                    else:
                        # No current database - list all accessible tables
                        query = """
                            SELECT 
                                table_schema,
                                table_name,
                                table_rows as row_count
                            FROM information_schema.tables
                            WHERE table_type = 'BASE TABLE'
                            ORDER BY table_schema, table_name
                        """
                        cur.execute(query)

                results = []
                for row in cur.fetchall():
                    results.append(
                        {
                            "schema": row[0],
                            "table": row[1],
                            "row_count": row[2] if row[2] is not None else None,
                        }
                    )

                conn.close()
                return results

        except Exception as e:
            raise ConnectionError(f"Failed to list tables from MySQL: {e}") from e
