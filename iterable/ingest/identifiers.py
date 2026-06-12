"""
SQL identifier validation and quoting helpers for ingest backends.

Table and column names cannot be passed as bound query parameters, so before
interpolating them into SQL statements they must be quoted and escaped to
prevent SQL injection through crafted identifiers.

Quoting strategy: wrap the identifier in the database's identifier quote
character ('"' for PostgreSQL/SQLite/DuckDB, '`' for MySQL) and escape any
embedded quote characters by doubling them. This is safe for arbitrary
identifier content while remaining compatible with real-world column names
(spaces, dashes, unicode). Control characters and NUL bytes are rejected.
"""

from __future__ import annotations

import re

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")


def validate_identifier(name: str, kind: str = "identifier") -> str:
    """
    Validate a SQL identifier (column name or one part of a table name).

    Args:
        name: Identifier to validate
        kind: Human-readable description used in error messages

    Returns:
        The validated identifier (unchanged)

    Raises:
        ValueError: If the identifier is empty, not a string, or contains control characters
    """
    if not isinstance(name, str) or not name:
        raise ValueError(f"Invalid {kind}: must be a non-empty string, got {name!r}")
    if _CONTROL_CHARS_RE.search(name):
        raise ValueError(f"Invalid {kind} {name!r}: control characters are not allowed")
    return name


def quote_identifier(name: str, quote_char: str = '"', kind: str = "identifier") -> str:
    """
    Validate, escape and quote a single SQL identifier.

    Embedded quote characters are escaped by doubling, which is the standard
    identifier-escaping rule for PostgreSQL, SQLite, DuckDB (") and MySQL (`).

    Args:
        name: Identifier to quote
        quote_char: Quote character ('"' for PostgreSQL/SQLite/DuckDB, '`' for MySQL)
        kind: Human-readable description used in error messages

    Returns:
        The quoted identifier, e.g. '"my_column"'
    """
    validate_identifier(name, kind=kind)
    escaped = name.replace(quote_char, quote_char * 2)
    return f"{quote_char}{escaped}{quote_char}"


def quote_table_name(table: str, quote_char: str = '"') -> str:
    """
    Validate and quote a table name, allowing an optional schema qualifier.

    Args:
        table: Table name, optionally schema-qualified ("schema.table")
        quote_char: Quote character for the target database

    Returns:
        The quoted table name, e.g. '"schema"."table"'

    Raises:
        ValueError: If the table name is empty or contains control characters
    """
    parts = table.split(".") if "." in table and table.count(".") == 1 else [table]
    return ".".join(quote_identifier(part, quote_char=quote_char, kind="table name") for part in parts)


def quote_columns(columns: list[str], quote_char: str = '"') -> list[str]:
    """
    Validate and quote a list of column names.

    Args:
        columns: Column names to quote
        quote_char: Quote character for the target database

    Returns:
        List of quoted column names
    """
    return [quote_identifier(col, quote_char=quote_char, kind="column name") for col in columns]
