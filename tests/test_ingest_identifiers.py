"""Tests for SQL identifier validation and quoting in ingest."""

import pytest

from iterable.ingest.identifiers import (
    quote_columns,
    quote_identifier,
    quote_table_name,
    validate_identifier,
)


class TestValidateIdentifier:
    def test_accepts_simple_names(self):
        assert validate_identifier("users") == "users"
        assert validate_identifier("col_1") == "col_1"

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="non-empty"):
            validate_identifier("")

    def test_rejects_control_characters(self):
        with pytest.raises(ValueError, match="control characters"):
            validate_identifier("bad\x00name")


class TestQuoteIdentifier:
    def test_quotes_postgres_style(self):
        assert quote_identifier("user") == '"user"'

    def test_escapes_embedded_quotes(self):
        assert quote_identifier('user"name') == '"user""name"'

    def test_mysql_backticks(self):
        assert quote_identifier("user", quote_char="`") == "`user`"


class TestQuoteTableName:
    def test_schema_qualified(self):
        assert quote_table_name("public.users") == '"public"."users"'

    def test_rejects_control_characters_in_schema(self):
        with pytest.raises(ValueError, match="control characters"):
            quote_table_name("public\x00users")


class TestQuoteColumns:
    def test_quotes_all_columns(self):
        assert quote_columns(["id", "name"]) == ['"id"', '"name"']
