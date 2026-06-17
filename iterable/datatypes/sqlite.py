from __future__ import annotations

import sqlite3
import typing
from typing import Any

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteError
from ..types import Row


class SQLiteIterable(BaseFileIterable):
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
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, noopen=True, options=options)
        self.table = table
        self.query = query
        if "table" in options:
            self.table = options["table"]
        if "query" in options:
            self.query = options["query"]
        if stream is not None:
            raise ReadError(
                "SQLite requires a filename, not a stream",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        if filename is None:
            raise ReadError(
                "SQLite requires a filename",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        self.connection = None
        self.cursor = None
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        if self.connection is not None:
            self.connection.close()

        self.connection = sqlite3.connect(self.filename)
        self.connection.row_factory = sqlite3.Row  # Return rows as dict-like objects

        if self.mode in ["w", "wr"]:
            # Write mode - initialize but don't create cursor yet
            # Table will be created on first write if needed
            self.cursor = None
            self.keys = None
        else:
            # Read mode
            if self.query:
                # Use custom query
                self.cursor = self.connection.execute(self.query)
            elif self.table:
                # Query specific table
                self.cursor = self.connection.execute(f"SELECT * FROM {self.table}")
            else:
                # Get first table
                cursor = self.connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name LIMIT 1"
                )
                first_table = cursor.fetchone()
                if first_table is None:
                    # No tables found - set cursor to None, will raise error on read()
                    self.table = None
                    self.cursor = None
                    self.keys = []
                    return
                self.table = first_table[0]
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
            count_cursor = self.connection.execute(f"SELECT COUNT(*) as count FROM ({self.query})")
            return count_cursor.fetchone()[0]
        elif self.table:
            count_cursor = self.connection.execute(f"SELECT COUNT(*) FROM {self.table}")
            return count_cursor.fetchone()[0]
        return 0

    @staticmethod
    def id() -> str:
        return "sqlite"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_tables() -> bool:
        """Indicates if this format supports multiple tables."""
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List available table names in the SQLite database.

        Args:
            filename: Optional filename. If None, uses instance's filename and reuses open connection.

        Returns:
            list[str]: List of table names, or empty list if no tables.
        """
        # If connection is already open, reuse it
        if filename is None and hasattr(self, "connection") and self.connection is not None:
            cursor = self.connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            return [row[0] for row in cursor.fetchall()]

        # Otherwise, open temporarily
        target_filename = filename if filename is not None else self.filename
        if target_filename is None:
            return None

        connection = sqlite3.connect(target_filename)
        try:
            cursor = connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            return [row[0] for row in cursor.fetchall()]
        finally:
            connection.close()

    def read(self, skip_empty: bool = True) -> dict:
        """Read single SQLite record"""
        if self.cursor is None:
            raise ValueError("No tables found in SQLite database")
        row = self.cursor.fetchone()
        if row is None:
            raise StopIteration
        # Convert Row to dict
        result = dict(zip(self.keys, row, strict=False))
        self.pos += 1
        return result

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk SQLite records using fetchmany for efficiency."""
        if self.cursor is None:
            return []
        rows = self.cursor.fetchmany(num)
        if not rows:
            return []
        chunk = [dict(zip(self.keys, row, strict=False)) for row in rows]
        self.pos += len(chunk)
        return chunk

    def write(self, record: Row) -> None:
        """Write single SQLite record"""
        if self.mode not in ["w", "wr"]:
            raise WriteError(
                "Write mode not enabled",
                filename=self.filename,
                error_code="INVALID_MODE",
            )
        if self.table is None:
            raise WriteError(
                "Table name required for writing",
                filename=self.filename,
                error_code="INVALID_PARAMETER",
            )
        if self._validation_hooks:
            validated = self._apply_validation_hooks(record)
            if validated is None:
                return
            record = validated

        if self.connection is None:
            self.connection = sqlite3.connect(self.filename)

        # Get column names from record keys or use existing keys
        if not hasattr(self, "keys") or self.keys is None:
            self.keys = list(record.keys())
            # Create table if it doesn't exist
            columns_def = ", ".join([f"{key} TEXT" for key in self.keys])
            create_query = f"CREATE TABLE IF NOT EXISTS {self.table} ({columns_def})"
            self.connection.execute(create_query)
            self.connection.commit()

        # Build INSERT statement
        columns = ", ".join(self.keys)
        placeholders = ", ".join(["?" for _ in self.keys])
        values = [record.get(key) for key in self.keys]

        insert_query = f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders})"
        self.connection.execute(insert_query, values)
        self.connection.commit()
        self.pos += 1

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk SQLite records"""
        if self.mode not in ["w", "wr"]:
            raise WriteError(
                "Write mode not enabled",
                filename=self.filename,
                error_code="INVALID_MODE",
            )
        if self.table is None:
            raise WriteError(
                "Table name required for writing",
                filename=self.filename,
                error_code="INVALID_PARAMETER",
            )

        if self.connection is None:
            self.connection = sqlite3.connect(self.filename)

        if self._validation_hooks:
            validated_records = []
            for record in records:
                validated = self._apply_validation_hooks(record)
                if validated is not None:
                    validated_records.append(validated)
            records = validated_records
        if not records:
            return

        # Get column names from first record or use existing keys
        if not hasattr(self, "keys") or self.keys is None:
            self.keys = list(records[0].keys())
            # Create table if it doesn't exist
            columns_def = ", ".join([f"{key} TEXT" for key in self.keys])
            create_query = f"CREATE TABLE IF NOT EXISTS {self.table} ({columns_def})"
            self.connection.execute(create_query)
            self.connection.commit()

        # Build INSERT statement
        columns = ", ".join(self.keys)
        placeholders = ", ".join(["?" for _ in self.keys])
        insert_query = f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders})"

        # Prepare all values
        all_values = [[record.get(key) for key in self.keys] for record in records]

        self.connection.executemany(insert_query, all_values)
        self.connection.commit()
        self.pos += len(records)

    def close(self):
        """Close SQLite connection"""
        if self.connection is not None:
            self.connection.close()
            self.connection = None
        super().close()
