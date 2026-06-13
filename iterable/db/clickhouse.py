"""
ClickHouse database driver.

Provides read-only access to ClickHouse databases as iterable data sources.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

from ..types import Row
from .base import DBDriver

# Imported at module level (guarded) so the optional dependency stays optional
# while remaining patchable as ``iterable.db.clickhouse.clickhouse_connect`` in tests.
try:
    import clickhouse_connect
except ImportError:  # pragma: no cover - exercised when dependency is absent
    clickhouse_connect = None


class ClickHouseDriver(DBDriver):
    """ClickHouse database driver.

    Supports streaming queries using batch processing for memory efficiency.
    Uses clickhouse-connect (official ClickHouse driver).
    """

    def __init__(self, source: str | Any, **kwargs: Any) -> None:
        """Initialize ClickHouse driver.

        Args:
            source: ClickHouse connection string (clickhouse://...) or existing clickhouse-connect client
            **kwargs: Additional parameters:
                - query: SQL query string or table name
                - batch_size: Number of rows per batch (default: 10000)
                - read_only: Validate queries are read-only (default: True)
                - database: Database name (if not in connection string)
                - table: Table name (alternative to query parameter)
                - columns: List of column names for projection
                - filter: WHERE clause fragment (e.g., "active = 1")
                - settings: ClickHouse query settings dict (e.g., {"max_threads": 4})
                - format: Result format ("native" or "JSONEachRow", default: "native")
                - connect_args: Additional arguments for clickhouse_connect.get_client()
        """
        super().__init__(source, **kwargs)
        self._column_names: list[str] | None = None

    def connect(self) -> None:
        """Establish ClickHouse connection.

        Raises:
            ImportError: If clickhouse-connect is not installed
            ConnectionError: If connection fails
        """
        # If source is already a client object, use it (no driver import needed)
        if hasattr(self.source, "query") and hasattr(self.source, "close"):
            self.conn = self.source
            self._connected = True
            return

        # Validate source type before requiring the driver dependency
        if not isinstance(self.source, str):
            raise ValueError(f"ClickHouse source must be a connection string or client object, got {type(self.source)}")

        if clickhouse_connect is None:
            raise ImportError(
                "clickhouse-connect is required for ClickHouse support. Install it with: pip install clickhouse-connect"
            )

        # Extract connection arguments
        connect_args = self.kwargs.get("connect_args", {})

        try:
            # Parse connection string
            # clickhouse://user:pass@host:port/database
            # clickhouse-connect can parse this format
            self.conn = clickhouse_connect.get_client(url=self.source, **connect_args)
            self._connected = True
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to ClickHouse: {e}") from e

    def _validate_read_only(self, query: str) -> None:
        """Validate that query is read-only (SELECT statement).

        Args:
            query: SQL query string

        Raises:
            ValueError: If query contains non-SELECT statements and read_only=True
        """
        read_only = self.kwargs.get("read_only", True)
        if not read_only:
            return

        # Check for non-SELECT statements using word boundaries to avoid false positives
        query_upper = query.upper().strip()

        # SQL keywords that modify data
        unsafe_keywords = [
            r"\bINSERT\b",
            r"\bUPDATE\b",
            r"\bDELETE\b",
            r"\bDROP\b",
            r"\bCREATE\b",
            r"\bALTER\b",
            r"\bTRUNCATE\b",
            r"\bREPLACE\b",
        ]

        # Check if query starts with SELECT or WITH (CTE)
        if not (query_upper.startswith("SELECT") or query_upper.startswith("WITH")):
            # Check for unsafe keywords
            for keyword_pattern in unsafe_keywords:
                if re.search(keyword_pattern, query_upper):
                    raise ValueError(
                        "Query contains non-SELECT statement and read_only=True. "
                        "Found unsafe keyword in query. Set read_only=False to allow non-SELECT queries."
                    )

    def _build_query(self) -> str:
        """Build SQL query from parameters.

        Returns:
            SQL query string
        """
        query = self.kwargs.get("query")
        table = self.kwargs.get("table")

        # If table parameter is provided, use it instead of query
        if table and not query:
            query = table

        if not query:
            raise ValueError("'query' or 'table' parameter is required for ClickHouse driver")

        # If query looks like a table name (no SQL keywords), build SELECT query
        query_upper = query.strip().upper()
        sql_keywords = {"SELECT", "WITH", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"}

        if not any(query_upper.startswith(kw) for kw in sql_keywords):
            # Treat as table name - build SELECT query
            database = self.kwargs.get("database")
            table_name = query.strip()

            # Build column list
            columns = self.kwargs.get("columns")
            if columns:
                col_list = ", ".join([self._quote_identifier(col) for col in columns])
            else:
                col_list = "*"

            # Build table reference
            if database:
                table_ref = f"{self._quote_identifier(database)}.{self._quote_identifier(table_name)}"
            else:
                table_ref = self._quote_identifier(table_name)

            # Build WHERE clause
            filter_clause = self.kwargs.get("filter")
            where_clause = f" WHERE {filter_clause}" if filter_clause else ""

            query = f"SELECT {col_list} FROM {table_ref}{where_clause}"

        return query

    def _quote_identifier(self, identifier: str) -> str:
        """Quote ClickHouse identifier.

        Args:
            identifier: Identifier to quote

        Returns:
            Quoted identifier
        """
        # ClickHouse uses backticks for identifiers
        # Escape backticks by doubling them
        escaped = identifier.replace("`", "``")
        return f"`{escaped}`"

    def iterate(self) -> Iterator[Row]:
        """Return iterator of dict rows from ClickHouse query.

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

        # Validate read-only if enabled
        try:
            self._validate_read_only(query)
        except Exception as e:
            self._handle_error(e, "validating query")
            if self._on_error == "raise":
                raise
            return

        # Get parameters
        batch_size = self.kwargs.get("batch_size", 10000)
        settings = self.kwargs.get("settings", {})
        result_format = self.kwargs.get("format", "native")
        database = self.kwargs.get("database")

        # Add max_block_size to settings if batch_size is specified
        if batch_size and "max_block_size" not in settings:
            settings = settings.copy()
            settings["max_block_size"] = batch_size

        # Start metrics
        self._start_metrics()

        try:
            # Execute query with settings
            # clickhouse-connect's query() method handles streaming internally via max_block_size
            # For very large datasets, consider using query_row_block_stream() in future
            if result_format == "JSONEachRow":
                # Use JSONEachRow format for text-based results
                query_with_format = f"{query} FORMAT JSONEachRow"
                result = self.conn.query(query_with_format, settings=settings, database=database)

                # Get column names
                if result.column_names:
                    self._column_names = result.column_names
                else:
                    self._column_names = []

                # For JSONEachRow, result.result_rows may contain dicts or tuples
                # Handle both cases
                for row in result.result_rows:
                    if isinstance(row, dict):
                        yield row
                    elif self._column_names:
                        yield dict(zip(self._column_names, row, strict=False))
                    else:
                        yield {str(i): val for i, val in enumerate(row)}
                    self._update_metrics(rows_read=1)
            else:
                # Use native format (default, more efficient)
                result = self.conn.query(query, settings=settings, database=database)

                # Get column names from result
                if result.column_names:
                    self._column_names = result.column_names
                else:
                    self._column_names = []

                # Iterate over result rows
                # clickhouse-connect returns rows as tuples
                for row in result.result_rows:
                    if self._column_names:
                        yield dict(zip(self._column_names, row, strict=False))
                    else:
                        # No column names - return as dict with numeric keys
                        yield {str(i): val for i, val in enumerate(row)}

                    self._update_metrics(rows_read=1)

        except Exception as e:
            self._handle_error(e, f"executing query: {query[:100]}")
            if self._on_error == "raise":
                raise

    def close(self) -> None:
        """Close ClickHouse connection and clean up resources."""
        # Close connection
        super().close()

    @staticmethod
    def list_tables(
        connection_string: str,
        database: str | None = None,
        **connect_args: Any,
    ) -> list[dict[str, Any]]:
        """List tables in ClickHouse database.

        Args:
            connection_string: ClickHouse connection string
            database: Optional database name (default: all databases)
            **connect_args: Additional connection arguments

        Returns:
            List of dicts with keys: database, table, row_count (estimate)

        Raises:
            ImportError: If clickhouse-connect is not installed
            ConnectionError: If connection fails
        """
        if clickhouse_connect is None:
            raise ImportError(
                "clickhouse-connect is required for ClickHouse support. Install it with: pip install clickhouse-connect"
            )

        try:
            client = clickhouse_connect.get_client(url=connection_string, **connect_args)

            # Query system.tables to get table list
            # ClickHouse uses string interpolation for parameters, but we'll use proper escaping
            if database:
                # Escape database name for safety
                db_escaped = database.replace("'", "''")
                query = f"""
                    SELECT 
                        database,
                        name as table,
                        total_rows as row_count
                    FROM system.tables
                    WHERE database = '{db_escaped}'
                    ORDER BY database, name
                """
            else:
                query = """
                    SELECT 
                        database,
                        name as table,
                        total_rows as row_count
                    FROM system.tables
                    WHERE database NOT IN ('system', 'information_schema', 'INFORMATION_SCHEMA')
                    ORDER BY database, name
                """
            result = client.query(query)

            results = []
            if result.column_names:
                col_names = result.column_names
                for row in result.result_rows:
                    row_dict = dict(zip(col_names, row, strict=False))
                    results.append(
                        {
                            "database": row_dict.get("database"),
                            "table": row_dict.get("table"),
                            "row_count": row_dict.get("row_count") if row_dict.get("row_count") is not None else None,
                        }
                    )
            else:
                # Fallback if column names not available
                for row in result.result_rows:
                    if len(row) >= 3:
                        results.append(
                            {
                                "database": row[0],
                                "table": row[1],
                                "row_count": row[2] if row[2] is not None else None,
                            }
                        )

            client.close()
            return results

        except Exception as e:
            raise ConnectionError(f"Failed to list tables from ClickHouse: {e}") from e
