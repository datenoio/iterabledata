"""
MySQL/MariaDB database driver.

Provides read-only access to MySQL/MariaDB databases as iterable data sources.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..types import Row
from .base import DBDriver
from .pooling import pool_enabled, pooled_acquire, pooled_release

# Imported at module level (guarded) so the optional dependency stays optional
# while remaining patchable as ``iterable.db.mysql.pymysql`` in tests.
try:
    import pymysql
except ImportError:  # pragma: no cover - exercised when dependency is absent
    pymysql = None


def _validate_connection(conn: Any) -> bool:
    """Validate that a pooled MySQL connection is still usable."""
    try:
        if hasattr(conn, "open") and not conn.open:
            return False
        conn.ping(reconnect=False)
        return True
    except Exception:
        return False


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
                - pool: Pool configuration dict (or bool) with keys:
                    - enabled: Enable connection pooling (default: False, opt-in)
                    - min_size: Minimum pool size (default: 1)
                    - max_size: Maximum pool size (default: 10)
                    - timeout: Connection acquisition timeout in seconds (default: 30.0)
                    - max_idle: Maximum idle time in seconds (default: 300.0)
                  Ignored when `source` is an existing connection object.
        """
        super().__init__(source, **kwargs)
        self._cursor: Any = None
        self._column_names: list[str] | None = None
        self._pool: Any = None
        self._pooled_conn: Any = None
        self._pooled_created_time: float | None = None

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

        # Extract pool configuration (opt-in: disabled by default)
        pool_config = self.kwargs.get("pool", {})
        use_pool = pool_enabled(pool_config, default=False)

        # Extract connection arguments
        connect_args = self._parse_connect_args()

        try:
            if use_pool:
                # Use connection pool
                pool_key = f"mysql:{self.source}"

                def factory():
                    """Factory function to create new MySQL connection."""
                    return pymysql.connect(**connect_args)

                config_dict = pool_config if isinstance(pool_config, dict) else {}
                self._pool, self._pooled_conn, self._pooled_created_time = pooled_acquire(
                    pool_key, factory, config_dict, validate=_validate_connection
                )
                self.conn = self._pooled_conn
            else:
                # Direct connection (no pooling)
                self.conn = pymysql.connect(**connect_args)
            self._connected = True

        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to MySQL: {e}") from e

    def _parse_connect_args(self) -> dict[str, Any]:
        """Build pymysql.connect() kwargs from connect_args and the connection URL."""
        connect_args = dict(self.kwargs.get("connect_args", {}))

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
        elif "://" not in self.source:
            # Assume it's a DSN string or use as host
            # For DSN strings, pymysql.connect() will parse them
            # For simple host strings, use as host
            connect_args["host"] = self.source

        return connect_args

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

            # col_list/table_ref quoted via _quote_identifier(); filter is an explicit raw-SQL pass-through parameter.
            query = f"SELECT {col_list} FROM {table_ref}{where_clause}"  # nosec B608

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

    def _prepare_query(self) -> str | None:
        """Build the query; returns None when the error policy skips."""
        try:
            return self._build_query()
        except Exception as e:
            self._handle_error(e, "building query")
            if self._on_error == "raise":
                raise
            return None

    def _open_cursor(self, server_side_cursor: bool) -> None:
        if server_side_cursor:
            # Use SSCursor (server-side cursor) for streaming
            self._cursor = self.conn.cursor(pymysql.cursors.SSCursor)
        else:
            self._cursor = self.conn.cursor()

    def _execute_query(self, query: str) -> bool:
        """Execute on the current cursor; False when the error policy skips."""
        try:
            self._cursor.execute(query)
            return True
        except Exception as e:
            self._handle_error(e, f"executing query: {query[:100]}")
            if self._on_error == "raise":
                raise
            return False

    def _set_column_names(self) -> None:
        if self._cursor.description:
            self._column_names = [desc[0] for desc in self._cursor.description]
        else:
            # No columns (e.g., INSERT, UPDATE without RETURNING)
            self._column_names = []

    def _yield_rows(self, rows: Any) -> Iterator[Row]:
        for row in rows:
            if self._column_names:
                yield dict(zip(self._column_names, row, strict=False))
            else:
                # No column names - return as tuple or empty dict
                yield {}

            self._update_metrics(rows_read=1)

    def _iterate_server_side(self, batch_size: int) -> Iterator[Row]:
        """For server-side cursors, fetch in batches."""
        while True:
            try:
                rows = self._cursor.fetchmany(batch_size)
                if not rows:
                    break

                yield from self._yield_rows(rows)
            except Exception as e:
                self._handle_error(e, "fetching rows")
                if self._on_error == "raise":
                    raise
                break

    def _iterate_client_side(self) -> Iterator[Row]:
        """For regular cursors, iterate directly."""
        try:
            yield from self._yield_rows(self._cursor)
        except Exception as e:
            self._handle_error(e, "iterating rows")
            if self._on_error == "raise":
                raise

    def _cleanup_cursor(self) -> None:
        """Clean up cursor."""
        if self._cursor is not None:
            try:
                self._cursor.close()
            except Exception:
                pass
            self._cursor = None

    def iterate(self) -> Iterator[Row]:
        """Return iterator of dict rows from MySQL query.

        Yields:
            dict: Database row as dictionary

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected or self.conn is None:
            raise RuntimeError("Not connected to database. Call connect() first.")

        query = self._prepare_query()
        if query is None:
            return

        # Get batch size
        batch_size = self.kwargs.get("batch_size", 10000)
        server_side_cursor = self.kwargs.get("server_side_cursor", True)

        # Start metrics
        self._start_metrics()

        try:
            # Create cursor
            self._open_cursor(server_side_cursor)

            # Execute query
            if not self._execute_query(query):
                return

            # Get column names
            self._set_column_names()

            # Iterate over results
            if server_side_cursor:
                yield from self._iterate_server_side(batch_size)
            else:
                yield from self._iterate_client_side()

        finally:
            self._cleanup_cursor()

    def close(self) -> None:
        """Close MySQL connection and clean up resources."""
        # Close cursor first
        if self._cursor is not None:
            try:
                self._cursor.close()
            except Exception:
                pass
            self._cursor = None

        # Return connection to pool if pooled, otherwise close directly
        if self._pool is not None and self._pooled_conn is not None and self._pooled_created_time is not None:
            pooled_release(self._pool, self._pooled_conn, self._pooled_created_time)
            self._pool = None
            self._pooled_conn = None
            self._pooled_created_time = None
            self.conn = None
            self._connected = False
            self._closed = True
        else:
            # Direct close (no pooling)
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
