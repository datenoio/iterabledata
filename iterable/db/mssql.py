"""
Microsoft SQL Server database driver.

Provides read-only access to Microsoft SQL Server databases as iterable data sources.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..types import Row
from .base import DBDriver


class MSSQLDriver(DBDriver):
    """Microsoft SQL Server database driver.

    Supports streaming queries using batch processing for memory efficiency.
    Uses pyodbc (ODBC driver for SQL Server).
    """

    def __init__(self, source: str | Any, **kwargs: Any) -> None:
        """Initialize MSSQL driver.

        Args:
            source: SQL Server connection string (mssql://..., odbc://..., or DSN) or existing pyodbc connection
            **kwargs: Additional parameters:
                - query: SQL query string or table name
                - batch_size: Number of rows per batch (default: 10000)
                - schema: Schema name for table references (default: 'dbo')
                - columns: List of column names for projection
                - filter: WHERE clause fragment (e.g., "active = 1")
                - connect_args: Additional arguments for pyodbc.connect()
        """
        super().__init__(source, **kwargs)
        self._cursor: Any = None
        self._column_names: list[str] | None = None

    def connect(self) -> None:
        """Establish SQL Server connection.

        Raises:
            ImportError: If pyodbc is not installed
            ConnectionError: If connection fails
        """
        try:
            import pyodbc
        except ImportError:
            raise ImportError(
                "pyodbc is required for SQL Server support. Install it with: pip install pyodbc"
            ) from None

        # If source is already a connection object, use it
        if hasattr(self.source, "cursor") and hasattr(self.source, "close"):
            self.conn = self.source
            self._connected = True
            return

        # Parse connection string
        if not isinstance(self.source, str):
            raise ValueError(
                f"SQL Server source must be a connection string or connection object, got {type(self.source)}"
            )

        # Extract connection arguments
        connect_args = self.kwargs.get("connect_args", {})

        try:
            # Parse connection string if it's a URL
            if (
                self.source.startswith("mssql://")
                or self.source.startswith("mssql+pyodbc://")
                or self.source.startswith("odbc://")
            ):
                # Parse URL format: mssql://user:pass@host:port/database?driver=ODBC+Driver+17+for+SQL+Server
                from urllib.parse import parse_qs, urlparse

                parsed = urlparse(self.source)
                conn_str_parts = []

                if parsed.username:
                    conn_str_parts.append(f"UID={parsed.username}")
                if parsed.password:
                    conn_str_parts.append(f"PWD={parsed.password}")
                if parsed.hostname:
                    conn_str_parts.append(f"SERVER={parsed.hostname}")
                if parsed.port:
                    conn_str_parts.append(f"PORT={parsed.port}")
                if parsed.path:
                    db_name = parsed.path.lstrip("/")
                    if db_name:
                        conn_str_parts.append(f"DATABASE={db_name}")

                # Parse query parameters
                query_params = parse_qs(parsed.query)
                if "driver" in query_params:
                    driver = query_params["driver"][0]
                    conn_str_parts.append(f"DRIVER={{{driver}}}")
                elif "DRIVER" not in str(connect_args):
                    # Default driver if not specified
                    conn_str_parts.append("DRIVER={ODBC Driver 17 for SQL Server}")

                # Add any additional connection args
                for key, value in connect_args.items():
                    if key.upper() not in ["UID", "PWD", "SERVER", "PORT", "DATABASE", "DRIVER"]:
                        conn_str_parts.append(f"{key}={value}")

                connection_string = ";".join(conn_str_parts)
                self.conn = pyodbc.connect(connection_string)
            else:
                # Assume it's a DSN or full connection string
                # Use as-is, or merge with connect_args
                if connect_args:
                    # If connect_args provided, merge with connection string
                    conn_str_parts = [self.source]
                    for key, value in connect_args.items():
                        conn_str_parts.append(f"{key}={value}")
                    connection_string = ";".join(conn_str_parts)
                    self.conn = pyodbc.connect(connection_string)
                else:
                    self.conn = pyodbc.connect(self.source)

            self._connected = True

        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to SQL Server: {e}") from e

    def _build_query(self) -> str:
        """Build SQL query from parameters.

        Returns:
            SQL query string
        """
        query = self.kwargs.get("query")
        if not query:
            raise ValueError("'query' parameter is required for SQL Server driver")

        # If query looks like a table name (no SQL keywords), build SELECT query
        query_upper = query.strip().upper()
        sql_keywords = {"SELECT", "WITH", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"}

        if not any(query_upper.startswith(kw) for kw in sql_keywords):
            # Treat as table name - build SELECT query
            schema = self.kwargs.get("schema", "dbo")
            table = query.strip()

            # Build column list
            columns = self.kwargs.get("columns")
            if columns:
                col_list = ", ".join([self._quote_identifier(col) for col in columns])
            else:
                col_list = "*"

            # Build table reference
            table_ref = f"{self._quote_identifier(schema)}.{self._quote_identifier(table)}"

            # Build WHERE clause
            filter_clause = self.kwargs.get("filter")
            where_clause = f" WHERE {filter_clause}" if filter_clause else ""

            query = f"SELECT {col_list} FROM {table_ref}{where_clause}"

        return query

    def _quote_identifier(self, identifier: str) -> str:
        """Quote SQL Server identifier.

        Args:
            identifier: Identifier to quote

        Returns:
            Quoted identifier
        """
        # SQL Server uses square brackets for identifiers
        # Escape closing brackets by doubling them
        escaped = identifier.replace("]", "]]")
        return f"[{escaped}]"

    def iterate(self) -> Iterator[Row]:
        """Return iterator of dict rows from SQL Server query.

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
                            # Convert row tuple to dict
                            # Handle pyodbc row objects
                            if hasattr(row, "_asdict"):
                                yield row._asdict()
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
        """Close SQL Server connection and clean up resources."""
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
        """List tables in SQL Server database.

        Args:
            connection_string: SQL Server connection string
            schema: Optional schema name (default: 'dbo')
            **connect_args: Additional connection arguments

        Returns:
            List of dicts with keys: schema, table, row_count (estimate)

        Raises:
            ImportError: If pyodbc is not installed
            ConnectionError: If connection fails
        """
        try:
            import pyodbc
        except ImportError:
            raise ImportError(
                "pyodbc is required for SQL Server support. Install it with: pip install pyodbc"
            ) from None

        try:
            # Parse connection string similar to connect()
            if (
                connection_string.startswith("mssql://")
                or connection_string.startswith("mssql+pyodbc://")
                or connection_string.startswith("odbc://")
            ):
                from urllib.parse import parse_qs, urlparse

                parsed = urlparse(connection_string)
                conn_str_parts = []

                if parsed.username:
                    conn_str_parts.append(f"UID={parsed.username}")
                if parsed.password:
                    conn_str_parts.append(f"PWD={parsed.password}")
                if parsed.hostname:
                    conn_str_parts.append(f"SERVER={parsed.hostname}")
                if parsed.port:
                    conn_str_parts.append(f"PORT={parsed.port}")
                if parsed.path:
                    db_name = parsed.path.lstrip("/")
                    if db_name:
                        conn_str_parts.append(f"DATABASE={db_name}")

                query_params = parse_qs(parsed.query)
                if "driver" in query_params:
                    driver = query_params["driver"][0]
                    conn_str_parts.append(f"DRIVER={{{driver}}}")
                elif "DRIVER" not in str(connect_args):
                    conn_str_parts.append("DRIVER={ODBC Driver 17 for SQL Server}")

                for key, value in connect_args.items():
                    if key.upper() not in ["UID", "PWD", "SERVER", "PORT", "DATABASE", "DRIVER"]:
                        conn_str_parts.append(f"{key}={value}")

                connection_string = ";".join(conn_str_parts)
                conn = pyodbc.connect(connection_string)
            else:
                if connect_args:
                    conn_str_parts = [connection_string]
                    for key, value in connect_args.items():
                        conn_str_parts.append(f"{key}={value}")
                    connection_string = ";".join(conn_str_parts)
                    conn = pyodbc.connect(connection_string)
                else:
                    conn = pyodbc.connect(connection_string)

            with conn.cursor() as cur:
                # Query system catalogs
                if schema:
                    query = """
                        SELECT 
                            TABLE_SCHEMA,
                            TABLE_NAME,
                            NULL as row_count
                        FROM INFORMATION_SCHEMA.TABLES
                        WHERE TABLE_SCHEMA = ?
                            AND TABLE_TYPE = 'BASE TABLE'
                        ORDER BY TABLE_SCHEMA, TABLE_NAME
                    """
                    cur.execute(query, (schema,))
                else:
                    query = """
                        SELECT 
                            TABLE_SCHEMA,
                            TABLE_NAME,
                            NULL as row_count
                        FROM INFORMATION_SCHEMA.TABLES
                        WHERE TABLE_TYPE = 'BASE TABLE'
                        ORDER BY TABLE_SCHEMA, TABLE_NAME
                    """
                    cur.execute(query)

                results = []
                for row in cur:
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
            raise ConnectionError(f"Failed to list tables from SQL Server: {e}") from e
