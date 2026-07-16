from __future__ import annotations

import os
import re
import typing
from typing import Any

import duckdb

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


def _default_table_name(filename: str | None) -> str:
    """Derive a safe SQL table name from the output filename.

    Used when writing to a database file without an explicit ``table`` so that
    conversions like ``convert(... , "data.ddb")`` work out of the box, creating
    a table named after the file (e.g. ``data.ddb`` -> ``data``).
    """
    if not filename:
        return "data"
    base = os.path.basename(str(filename))
    stem = base.rsplit(".", 1)[0] if "." in base else base
    sanitized = re.sub(r"\W", "_", stem)
    if not sanitized:
        return "data"
    if sanitized[0].isdigit():
        sanitized = "_" + sanitized
    return sanitized


class DuckDBDatabaseIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode="r",
        table: str | None = None,
        query: str | None = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        # Validate before BaseFileIterable initializes, to avoid BaseFileIterable failing
        # when no source is provided.
        if stream is not None:
            raise ValueError("DuckDB requires a filename, not a stream")
        if filename is None:
            raise ValueError("DuckDB requires a filename")
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, noopen=True, options=options)
        self.table = table
        self.query = query
        if "table" in options:
            self.table = options["table"]
        if "query" in options:
            self.query = options["query"]
        self.connection = None
        self.cursor = None
        self._no_tables = False
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        if self.connection is not None:
            self.connection.close()

        self.connection = duckdb.connect(self.filename)

        if self.mode in ["w", "wr"]:
            # Write mode - initialize but don't create cursor yet
            # Table will be created on first write if needed.  The database
            # class keeps the filename-derived default for bulk conversions;
            # the backwards-compatible ``DuckDBIterable`` alias below still
            # requires an explicit table for its single-row ``write`` API.
            self.cursor = None
            self.keys = None
            if self.table is None:
                self.table = _default_table_name(self.filename)
        else:
            # Read mode
            if self.query:
                # Use custom query
                self._no_tables = False
                self.cursor = self.connection.execute(self.query)
            elif self.table:
                # Query specific table
                self._no_tables = False
                self.cursor = self.connection.execute(f"SELECT * FROM {self.table}")
            else:
                # Get first table - DuckDB supports SHOW TABLES
                try:
                    tables = self.connection.execute("SHOW TABLES").fetchall()
                except Exception:
                    # Fallback to information_schema if SHOW TABLES doesn't work
                    tables = self.connection.execute(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'main' ORDER BY table_name LIMIT 1"
                    ).fetchall()
                if not tables:
                    # Defer raising until read(), so callers can construct the iterable.
                    self._no_tables = True
                    self.cursor = None
                    self.keys = None
                    self.pos = 0
                    return
                self._no_tables = False
                self.table = tables[0][0]
                self.cursor = self.connection.execute(f"SELECT * FROM {self.table}")

            # Get column names from cursor description
            if self.cursor.description:
                self.keys = [description[0] for description in self.cursor.description]
            else:
                self.keys = None
        self.pos = 0

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if self.query:
            # For custom queries, we need to count manually
            count_result = self.connection.execute(f"SELECT COUNT(*) as count FROM ({self.query})").fetchone()
            return count_result[0] if count_result else 0
        elif self.table:
            count_result = self.connection.execute(f"SELECT COUNT(*) FROM {self.table}").fetchone()
            return count_result[0] if count_result else 0
        return 0

    @staticmethod
    def id() -> str:
        return "duckdb"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_tables() -> bool:
        """Indicates if this format supports multiple tables."""
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List available table names in the DuckDB database.

        Args:
            filename: Optional filename. If None, uses instance's filename and reuses open connection.

        Returns:
            list[str]: List of table names, or empty list if no tables.
        """
        # If connection is already open, reuse it
        if filename is None and hasattr(self, "connection") and self.connection is not None:
            try:
                tables = self.connection.execute("SHOW TABLES").fetchall()
            except Exception:
                # Fallback to information_schema
                tables = self.connection.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name"
                ).fetchall()
            return [row[0] for row in tables]

        # Otherwise, open temporarily
        target_filename = filename if filename is not None else self.filename
        if target_filename is None:
            return None

        connection = duckdb.connect(target_filename)
        try:
            try:
                tables = connection.execute("SHOW TABLES").fetchall()
            except Exception:
                # Fallback to information_schema
                tables = connection.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name"
                ).fetchall()
            return [row[0] for row in tables]
        finally:
            connection.close()

    def read(self, skip_empty: bool = True) -> dict:
        """Read single DuckDB record"""
        if self._no_tables:
            raise ValueError("No tables found in DuckDB database file")
        row = self.cursor.fetchone()
        if row is None:
            raise StopIteration
        # Convert row tuple to dict
        result = dict(zip(self.keys, row, strict=False))
        self.pos += 1
        return result

    def write(self, record: Row) -> None:
        """Write single DuckDB record"""
        if self.mode not in ["w", "wr"]:
            raise ValueError("Write mode not enabled")
        if self.table is None:
            raise ValueError("Table name required for writing")

        if self.connection is None:
            self.connection = duckdb.connect(self.filename)

        # Get column names from record keys or use existing keys
        if not hasattr(self, "keys") or self.keys is None:
            self.keys = list(record.keys())

            # Create table if it doesn't exist
            def _duckdb_type_from_value(v):
                # bool is a subclass of int, so check it first
                if isinstance(v, bool):
                    return "BOOLEAN"
                if isinstance(v, int):
                    return "BIGINT"
                if isinstance(v, float):
                    return "DOUBLE"
                return "VARCHAR"

            columns_def = ", ".join([f"{key} {_duckdb_type_from_value(record.get(key))}" for key in self.keys])
            create_query = f"CREATE TABLE IF NOT EXISTS {self.table} ({columns_def})"
            self.connection.execute(create_query)
            # DuckDB auto-commits, but commit() may exist for compatibility
            if hasattr(self.connection, "commit"):
                self.connection.commit()

        # Build INSERT statement
        columns = ", ".join(self.keys)
        placeholders = ", ".join(["?" for _ in self.keys])
        values = [record.get(key) for key in self.keys]

        insert_query = f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders})"
        self.connection.execute(insert_query, values)
        # DuckDB auto-commits, but commit() may exist for compatibility
        if hasattr(self.connection, "commit"):
            self.connection.commit()
        self.pos += 1

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk DuckDB records"""
        if self.mode not in ["w", "wr"]:
            raise ValueError("Write mode not enabled")
        if self.table is None:
            raise ValueError("Table name required for writing")

        if self.connection is None:
            self.connection = duckdb.connect(self.filename)

        if not records:
            return

        # Get column names from first record or use existing keys
        if not hasattr(self, "keys") or self.keys is None:
            self.keys = list(records[0].keys())

            # Create table if it doesn't exist
            def _duckdb_type_from_value(v):
                # bool is a subclass of int, so check it first
                if isinstance(v, bool):
                    return "BOOLEAN"
                if isinstance(v, int):
                    return "BIGINT"
                if isinstance(v, float):
                    return "DOUBLE"
                return "VARCHAR"

            first = records[0]
            columns_def = ", ".join([f"{key} {_duckdb_type_from_value(first.get(key))}" for key in self.keys])
            create_query = f"CREATE TABLE IF NOT EXISTS {self.table} ({columns_def})"
            self.connection.execute(create_query)
            # DuckDB auto-commits, but commit() may exist for compatibility
            if hasattr(self.connection, "commit"):
                self.connection.commit()

        # Build INSERT statement
        columns = ", ".join(self.keys)
        placeholders = ", ".join(["?" for _ in self.keys])
        insert_query = f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders})"

        # Prepare all values
        all_values = [[record.get(key) for key in self.keys] for record in records]

        self.connection.executemany(insert_query, all_values)
        # DuckDB auto-commits, but commit() may exist for compatibility
        if hasattr(self.connection, "commit"):
            self.connection.commit()
        self.pos += len(records)

    def close(self):
        """Close DuckDB connection"""
        if self.connection is not None:
            self.connection.close()
            self.connection = None
        super().close()


class DuckDBIterable(DuckDBDatabaseIterable):
    """Datatype facade retaining the legacy single-row table contract."""

    def __init__(self, *args, **kwargs):
        mode = kwargs.get("mode", "r")
        table = kwargs.get("table")
        options = kwargs.get("options") or {}
        explicit_table = table is not None or options.get("table") is not None
        super().__init__(*args, **kwargs)
        self._require_explicit_table_for_row_write = mode in ("w", "wr") and not explicit_table

    def write(self, record: Row) -> None:
        if getattr(self, "_require_explicit_table_for_row_write", False):
            raise ValueError("Table name required for writing")
        super().write(record)
