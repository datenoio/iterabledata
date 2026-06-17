from __future__ import annotations

import re
import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class MySQLDumpIterable(BaseFileIterable):
    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf8",
        table_name: str | None = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        self.table_name = table_name
        if "table_name" in options:
            self.table_name = options["table_name"]
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            self.entries = []
            current_table = None
            in_insert = False

            for line in self.fobj:
                line = line.strip()

                # Detect table name from INSERT INTO statement
                insert_match = re.match(r"INSERT\s+INTO\s+`?(\w+)`?", line, re.IGNORECASE)
                if insert_match:
                    current_table = insert_match.group(1)
                    if self.table_name and current_table != self.table_name:
                        continue
                    in_insert = True
                    # Extract values from INSERT statement
                    values_match = re.search(r"VALUES\s+(.+)", line, re.IGNORECASE)
                    if values_match:
                        values_str = values_match.group(1)
                        # Parse values
                        parsed_values = self._parse_values(values_str)
                        for values in parsed_values:
                            entry = {"_table": current_table}
                            entry.update(values)
                            self.entries.append(entry)
                    continue

                # Continue parsing multi-line INSERT
                if in_insert:
                    if line.endswith(";"):
                        in_insert = False
                        line = line.rstrip(";")

                    # Parse values from line
                    parsed_values = self._parse_values(line)
                    for values in parsed_values:
                        entry = {"_table": current_table}
                        entry.update(values)
                        self.entries.append(entry)

            self.iterator = iter(self.entries)
        else:
            self.entries = []
            self.current_table = None

    @staticmethod
    def id() -> str:
        return "mysqldump"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def _parse_values(self, values_str):
        """Parse VALUES clause from INSERT statement"""
        # Remove VALUES keyword if present
        values_str = re.sub(r"^\s*VALUES\s+", "", values_str, flags=re.IGNORECASE)
        # Remove trailing semicolon (common at end of INSERT statements)
        values_str = values_str.strip()
        if values_str.endswith(";"):
            values_str = values_str[:-1]

        # Split by ),( to get individual rows
        rows = []
        current_row = []
        current_value = ""
        paren_depth = 0
        in_quotes = False
        quote_char = None

        i = 0
        while i < len(values_str):
            char = values_str[i]

            if char in ("'", '"') and (i == 0 or values_str[i - 1] != "\\"):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                current_value += char
            elif not in_quotes:
                if char == "(":
                    paren_depth += 1
                    if paren_depth == 1:
                        current_value = ""
                        i += 1
                        continue
                    current_value += char
                elif char == ")":
                    paren_depth -= 1
                    if paren_depth == 0:
                        # End of row
                        current_row.append(current_value.strip())
                        rows.append(current_row)
                        current_row = []
                        current_value = ""
                        # Skip comma and whitespace after )
                        i += 1
                        while i < len(values_str) and values_str[i] in (",", " ", "\t", "\n"):
                            i += 1
                        continue
                    current_value += char
                elif char == "," and paren_depth == 1:
                    current_row.append(current_value.strip())
                    current_value = ""
                else:
                    current_value += char
            else:
                current_value += char

            i += 1

        # Parse values into dictionaries (we need column names, but they're in INSERT statement)
        # For now, return as list of lists - caller should handle column mapping
        result = []
        for row in rows:
            # Parse individual values
            parsed_row = self._parse_row_values(row)
            result.append(parsed_row)

        return result

    def _parse_row_values(self, row_str_list):
        """Parse a list of value strings into a dictionary"""
        # Since we don't have column names from INSERT, use numeric keys
        result = {}
        for idx, value_str in enumerate(row_str_list):
            # Remove quotes and unescape
            value_str = value_str.strip()
            if value_str.startswith("'") and value_str.endswith("'"):
                value_str = value_str[1:-1].replace("\\'", "'").replace("\\\\", "\\")
            elif value_str.startswith('"') and value_str.endswith('"'):
                value_str = value_str[1:-1].replace('\\"', '"').replace("\\\\", "\\")
            elif value_str.upper() == "NULL":
                value_str = None

            result[f"col_{idx}"] = value_str

        return result

    def read(self, skip_empty: bool = True) -> dict:
        """Read single MySQL dump record"""
        row = next(self.iterator)
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        """Write single MySQL dump record"""
        table = record.pop("_table", "data")

        if self.current_table != table:
            if self.current_table is not None:
                self.fobj.write(";\n")
            self.fobj.write(f"INSERT INTO `{table}` VALUES\n")
            self.current_table = table
            self.first_row = True
        else:
            self.fobj.write(",\n")

        # Build VALUES clause
        values = []
        for _key, value in record.items():
            if value is None:
                values.append("NULL")
            elif isinstance(value, str):
                # Escape quotes
                escaped = value.replace("'", "\\'").replace("\\", "\\\\")
                values.append(f"'{escaped}'")
            else:
                values.append(str(value))

        values_str = "(" + ",".join(values) + ")"
        if self.first_row:
            self.fobj.write(f"  {values_str}")
            self.first_row = False
        else:
            self.fobj.write(f"  {values_str}")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk MySQL dump records"""
        for record in records:
            self.write(record)
        if self.current_table:
            self.fobj.write(";\n")
