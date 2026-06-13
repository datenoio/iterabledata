"""
PostgreSQL database driver.

Provides read-only access to PostgreSQL databases as iterable data sources.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..types import Row
from .base import DBDriver
from .pooling import get_pool

# Imported at module level (guarded) so the optional dependency stays optional
# while remaining patchable as ``iterable.db.postgres.psycopg2`` in tests.
try:
    import psycopg2
except ImportError:  # pragma: no cover - exercised when dependency is absent
    psycopg2 = None


class PostgresDriver(DBDriver):
    """PostgreSQL database driver.

    Supports streaming queries using server-side cursors for memory efficiency.
    """

    def __init__(self, source: str | Any, **kwargs: Any) -> None:
        """Initialize PostgreSQL driver.

        Args:
            source: PostgreSQL connection string (postgresql://...) or existing psycopg2 connection
            **kwargs: Additional parameters:
                - query: SQL query string or table name
                - batch_size: Number of rows per batch (default: 10000)
                - read_only: Use read-only transaction (default: True)
                - schema: Schema name for table references
                - columns: List of column names for projection
                - filter: WHERE clause fragment (e.g., "active = TRUE")
                - server_side_cursor: Use server-side cursor (default: True)
                - connect_args: Additional arguments for psycopg2.connect()
                - pool: Pool configuration dict with keys:
                    - enabled: Enable connection pooling (default: True)
                    - min_size: Minimum pool size (default: 1)
                    - max_size: Maximum pool size (default: 10)
                    - timeout: Connection acquisition timeout in seconds (default: 30.0)
                    - max_idle: Maximum idle time in seconds (default: 300.0)
        """
        super().__init__(source, **kwargs)
        self._cursor: Any = None
        self._column_names: list[str] | None = None
        self._pool: Any = None
        self._pooled_conn: Any = None
        self._pooled_created_time: float | None = None

    def connect(self) -> None:
        """Establish PostgreSQL connection.

        Raises:
            ImportError: If psycopg2 is not installed
            ConnectionError: If connection fails
        """
        # If source is already a connection object, use it (no pooling). This
        # path does not require psycopg2 to be importable.
        if hasattr(self.source, "cursor") and hasattr(self.source, "close"):
            self.conn = self.source
            self._connected = True
            return

        # Validate source type before requiring the driver dependency
        if not isinstance(self.source, str):
            raise ValueError(
                f"PostgreSQL source must be a connection string or connection object, got {type(self.source)}"
            )

        if psycopg2 is None:
            raise ImportError(
                "psycopg2-binary is required for PostgreSQL support. Install it with: pip install psycopg2-binary"
            )
        ISOLATION_LEVEL_READ_COMMITTED = psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED

        # Extract pool configuration
        pool_config = self.kwargs.get("pool", {})
        use_pool = pool_config.get("enabled", True) if isinstance(pool_config, dict) else bool(pool_config)

        # Extract connection arguments
        connect_args = self.kwargs.get("connect_args", {})
        read_only = self.kwargs.get("read_only", True)

        try:
            if use_pool:
                # Use connection pool
                pool_key = f"postgres:{self.source}"

                def factory():
                    """Factory function to create new PostgreSQL connection."""
                    conn = psycopg2.connect(self.source, **connect_args)
                    # Set read-only transaction if requested
                    if read_only:
                        conn.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
                        with conn.cursor() as cur:
                            cur.execute("SET TRANSACTION READ ONLY")
                            conn.commit()
                    return conn

                def validate(conn: Any) -> bool:
                    """Validate PostgreSQL connection."""
                    try:
                        # Check if connection is closed
                        if hasattr(conn, "closed") and conn.closed:
                            return False
                        # Try a simple query
                        with conn.cursor() as cur:
                            cur.execute("SELECT 1")
                        return True
                    except Exception:
                        return False

                # Get pool configuration
                pool_cfg = {
                    "min_size": pool_config.get("min_size", 1) if isinstance(pool_config, dict) else 1,
                    "max_size": pool_config.get("max_size", 10) if isinstance(pool_config, dict) else 10,
                    "timeout": pool_config.get("timeout", 30.0) if isinstance(pool_config, dict) else 30.0,
                    "max_idle": pool_config.get("max_idle", 300.0) if isinstance(pool_config, dict) else 300.0,
                    "validate": validate,
                }

                self._pool = get_pool(pool_key, factory, pool_cfg)
                self._pooled_conn, self._pooled_created_time = self._pool.acquire()
                self.conn = self._pooled_conn
            else:
                # Direct connection (no pooling)
                self.conn = psycopg2.connect(self.source, **connect_args)
                # Set read-only transaction if requested (default: True)
                if read_only:
                    # Set transaction to read-only
                    self.conn.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
                    with self.conn.cursor() as cur:
                        cur.execute("SET TRANSACTION READ ONLY")
                        self.conn.commit()

            self._connected = True
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}") from e

    def _build_query(self) -> str:
        """Build SQL query from parameters.

        Returns:
            SQL query string
        """
        query = self.kwargs.get("query")
        if not query:
            raise ValueError("'query' parameter is required for PostgreSQL driver")

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
        """Quote PostgreSQL identifier.

        Args:
            identifier: Identifier to quote

        Returns:
            Quoted identifier
        """
        # Simple quoting - replace " with "" and wrap in double quotes
        escaped = identifier.replace('"', '""')
        return f'"{escaped}"'

    def iterate(self) -> Iterator[Row]:
        """Return iterator of dict rows from PostgreSQL query.

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
                # Use named server-side cursor for streaming
                self._cursor = self.conn.cursor(name="iterabledata_cursor")
                self._cursor.itersize = batch_size
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
        """Close PostgreSQL connection and clean up resources."""
        # Close cursor first
        if self._cursor is not None:
            try:
                self._cursor.close()
            except Exception:
                pass
            self._cursor = None

        # Return connection to pool if pooled, otherwise close directly
        if self._pool and self._pooled_conn is not None and self._pooled_created_time is not None:
            try:
                self._pool.release(self._pooled_conn, self._pooled_created_time)
            except Exception:
                # If release fails, try to close connection directly
                try:
                    if hasattr(self._pooled_conn, "close"):
                        self._pooled_conn.close()
                except Exception:
                    pass
            finally:
                self._pooled_conn = None
                self._pooled_created_time = None
                self._pool = None
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
        """List tables in PostgreSQL database.

        Args:
            connection_string: PostgreSQL connection string
            schema: Optional schema name (default: current schema)
            **connect_args: Additional connection arguments

        Returns:
            List of dicts with keys: schema, table, row_count (estimate)

        Raises:
            ImportError: If psycopg2 is not installed
            ConnectionError: If connection fails
        """
        if psycopg2 is None:
            raise ImportError(
                "psycopg2-binary is required for PostgreSQL support. Install it with: pip install psycopg2-binary"
            )

        try:
            conn = psycopg2.connect(connection_string, **connect_args)
            with conn.cursor() as cur:
                # Query system catalogs
                if schema:
                    query = """
                        SELECT 
                            table_schema,
                            table_name,
                            COALESCE(n_live_tup, 0) as row_count
                        FROM information_schema.tables t
                        LEFT JOIN pg_stat_user_tables s 
                            ON s.schemaname = t.table_schema 
                            AND s.relname = t.table_name
                        WHERE table_schema = %s
                            AND table_type = 'BASE TABLE'
                        ORDER BY table_schema, table_name
                    """
                    cur.execute(query, (schema,))
                else:
                    query = """
                        SELECT 
                            table_schema,
                            table_name,
                            COALESCE(n_live_tup, 0) as row_count
                        FROM information_schema.tables t
                        LEFT JOIN pg_stat_user_tables s 
                            ON s.schemaname = t.table_schema 
                            AND s.relname = t.table_name
                        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                            AND table_type = 'BASE TABLE'
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
            raise ConnectionError(f"Failed to list tables from PostgreSQL: {e}") from e
