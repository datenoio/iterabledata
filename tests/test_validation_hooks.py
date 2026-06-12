"""Tests for validation hooks."""

import pytest

from iterable.helpers.detect import open_iterable
from iterable.helpers.validation import rules_validator, schema_validator


class TestValidationHooksBasic:
    """Test basic validation hook functionality."""

    def test_validation_hook_raises_on_invalid(self, tmp_path):
        """Test validation hook raises exception on invalid data."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("col1,col2\n1,2\ninvalid,4\n")

        def validate_hook(row):
            if row.get("col1") == "invalid":
                raise ValueError("Invalid col1 value")
            return row

        with open_iterable(
            str(input_file), iterableargs={"validation_hook": validate_hook, "on_validation_error": "raise"}
        ) as source:
            rows = []
            with pytest.raises(ValueError, match="Invalid col1 value"):
                for row in source:
                    rows.append(row)

        # Should have processed first row before hitting invalid row
        assert len(rows) == 1
        assert rows[0]["col1"] == "1"

    def test_validation_hook_skip_invalid(self, tmp_path):
        """Test validation hook skips invalid rows."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("col1,col2\n1,2\ninvalid,4\n5,6\n")

        def validate_hook(row):
            if row.get("col1") == "invalid":
                raise ValueError("Invalid col1 value")
            return row

        with open_iterable(
            str(input_file), iterableargs={"validation_hook": validate_hook, "on_validation_error": "skip"}
        ) as source:
            rows = list(source)

        # Should skip invalid row, keep valid ones
        assert len(rows) == 2
        assert rows[0]["col1"] == "1"
        assert rows[1]["col1"] == "5"

    def test_validation_hook_log_invalid(self, tmp_path, caplog):
        """Test validation hook logs invalid rows."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("col1,col2\n1,2\ninvalid,4\n5,6\n")

        def validate_hook(row):
            if row.get("col1") == "invalid":
                raise ValueError("Invalid col1 value")
            return row

        with open_iterable(
            str(input_file), iterableargs={"validation_hook": validate_hook, "on_validation_error": "log"}
        ) as source:
            rows = list(source)

        # Should process all rows, but log errors
        assert len(rows) == 3  # All rows processed
        assert "Validation failed" in caplog.text

    def test_validation_hook_warn_invalid(self, tmp_path):
        """Test validation hook warns on invalid rows."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("col1,col2\n1,2\ninvalid,4\n5,6\n")

        def validate_hook(row):
            if row.get("col1") == "invalid":
                raise ValueError("Invalid col1 value")
            return row

        with pytest.warns(UserWarning, match="Validation failed"):
            with open_iterable(
                str(input_file), iterableargs={"validation_hook": validate_hook, "on_validation_error": "warn"}
            ) as source:
                rows = list(source)

        # Should process all rows
        assert len(rows) == 3

    def test_multiple_validation_hooks(self, tmp_path):
        """Test multiple validation hooks chained together."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("col1,col2\n1,2\n3,4\n")

        def hook1(row):
            if int(row["col1"]) < 0:
                raise ValueError("col1 must be positive")
            return row

        def hook2(row):
            if int(row["col2"]) < 0:
                raise ValueError("col2 must be positive")
            return row

        with open_iterable(
            str(input_file), iterableargs={"validation_hook": [hook1, hook2], "on_validation_error": "raise"}
        ) as source:
            rows = list(source)

        assert len(rows) == 2


class TestRulesValidator:
    """Test rules_validator factory function."""

    def test_rules_validator_basic(self, tmp_path):
        """Test rules_validator with basic rules."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("email,url\nuser@example.com,https://example.com\ninvalid,invalid\n")

        rules = {"email": ["common.email"], "url": ["common.url"]}
        hook = rules_validator(rules)

        with open_iterable(
            str(input_file), iterableargs={"validation_hook": hook, "on_validation_error": "skip"}
        ) as source:
            rows = list(source)

        # Should skip invalid row
        assert len(rows) == 1
        assert rows[0]["email"] == "user@example.com"

    def test_rules_validator_required(self, tmp_path):
        """Test rules_validator with required rule."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("name,email\nJohn,john@example.com\n,missing@example.com\n")

        rules = {"name": ["required"]}
        hook = rules_validator(rules)

        with open_iterable(
            str(input_file), iterableargs={"validation_hook": hook, "on_validation_error": "skip"}
        ) as source:
            rows = list(source)

        # Should skip row with missing name
        assert len(rows) == 1
        assert rows[0]["name"] == "John"


class TestSchemaValidator:
    """Test schema_validator factory function."""

    def test_schema_validator_basic(self, tmp_path):
        """Test schema_validator with basic schema."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("name,age\nJohn,30\nJane,25\n")

        schema = {
            "fields": {
                "name": {"type": "str", "nullable": False},
                "age": {"type": "int", "nullable": False},
            }
        }
        hook = schema_validator(schema)

        with open_iterable(
            str(input_file), iterableargs={"validation_hook": hook, "on_validation_error": "raise"}
        ) as source:
            rows = list(source)

        assert len(rows) == 2

    def test_schema_validator_type_checking(self, tmp_path):
        """Test schema_validator with type checking."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("name,age\nJohn,30\nJane,not_a_number\n")

        schema = {
            "fields": {
                "name": {"type": "str", "nullable": False},
                "age": {"type": "int", "nullable": False},
            }
        }
        hook = schema_validator(schema)

        with open_iterable(
            str(input_file), iterableargs={"validation_hook": hook, "on_validation_error": "skip"}
        ) as source:
            rows = list(source)

        # Should skip row with invalid age type
        assert len(rows) == 1
        assert rows[0]["name"] == "John"


class TestValidationHooksWrite:
    """Test validation hooks during write operations."""

    def test_validation_hook_on_write(self, tmp_path):
        """Test validation hook applied during write."""
        output_file = tmp_path / "output.csv"

        def validate_hook(row):
            if "id" not in row:
                raise ValueError("Row missing required 'id' field")
            return row

        with open_iterable(
            str(output_file),
            mode="w",
            iterableargs={"validation_hook": validate_hook, "on_validation_error": "skip", "keys": ["id", "name"]},
        ) as dest:
            # Valid row - should be written
            dest.write({"id": 1, "name": "test"})

            # Invalid row - should be skipped
            dest.write({"name": "no_id"})

            # Another valid row
            dest.write({"id": 2, "name": "test2"})

        # Read back and verify
        with open_iterable(str(output_file)) as source:
            rows = list(source)

        # Should only have 2 rows (invalid one skipped)
        assert len(rows) == 2
        assert rows[0]["id"] == "1"
        assert rows[1]["id"] == "2"

    def test_validation_hook_on_write_bulk(self, tmp_path):
        """Test validation hook applied during write_bulk."""
        output_file = tmp_path / "output.csv"

        def validate_hook(row):
            if "id" not in row:
                raise ValueError("Row missing required 'id' field")
            return row

        with open_iterable(
            str(output_file),
            mode="w",
            iterableargs={"validation_hook": validate_hook, "on_validation_error": "skip", "keys": ["id", "name"]},
        ) as dest:
            dest.write_bulk(
                [
                    {"id": 1, "name": "test1"},
                    {"name": "no_id"},  # Invalid - should be skipped
                    {"id": 2, "name": "test2"},
                ]
            )

        # Read back and verify
        with open_iterable(str(output_file)) as source:
            rows = list(source)

        # Should only have 2 rows
        assert len(rows) == 2
        assert rows[0]["id"] == "1"
        assert rows[1]["id"] == "2"


class TestValidationHooksWriteFormats:
    """Test validation hooks during write for JSON, Parquet, SQLite, TopoJSON."""

    def _validate_id_required(self, row):
        if "id" not in row:
            raise ValueError("Row missing required 'id' field")
        return row

    def test_validation_hook_on_write_json(self, tmp_path):
        """Validation hook is applied when writing JSON."""
        output_file = tmp_path / "out.json"
        with open_iterable(
            str(output_file),
            mode="w",
            iterableargs={"validation_hook": self._validate_id_required, "on_validation_error": "skip"},
        ) as dest:
            dest.write({"id": 1, "name": "a"})
            dest.write({"name": "no_id"})
            dest.write({"id": 2, "name": "b"})
        with open_iterable(str(output_file)) as src:
            rows = list(src)
        assert len(rows) == 2
        assert rows[0]["id"] == 1 and rows[1]["id"] == 2

    def test_validation_hook_on_write_bulk_json(self, tmp_path):
        """Validation hook is applied when writing JSON bulk."""
        output_file = tmp_path / "out.json"
        with open_iterable(
            str(output_file),
            mode="w",
            iterableargs={"validation_hook": self._validate_id_required, "on_validation_error": "skip"},
        ) as dest:
            dest.write_bulk(
                [
                    {"id": 1, "name": "a"},
                    {"name": "no_id"},
                    {"id": 2, "name": "b"},
                ]
            )
        with open_iterable(str(output_file)) as src:
            rows = list(src)
        assert len(rows) == 2
        assert rows[0]["id"] == 1 and rows[1]["id"] == 2

    def test_validation_hook_on_write_jsonl(self, tmp_path):
        """Validation hook is applied when writing JSONL."""
        output_file = tmp_path / "out.jsonl"
        with open_iterable(
            str(output_file),
            mode="w",
            iterableargs={"validation_hook": self._validate_id_required, "on_validation_error": "skip"},
        ) as dest:
            dest.write({"id": 1, "name": "a"})
            dest.write({"name": "no_id"})
            dest.write({"id": 2, "name": "b"})
        with open_iterable(str(output_file)) as src:
            rows = list(src)
        assert len(rows) == 2
        assert rows[0]["id"] == 1 and rows[1]["id"] == 2

    def test_validation_hook_on_write_parquet(self, tmp_path):
        """Validation hook is applied when writing Parquet."""
        pytest.importorskip("pyarrow", reason="pyarrow required for Parquet")
        output_file = tmp_path / "out.parquet"
        with open_iterable(
            str(output_file),
            mode="w",
            iterableargs={"validation_hook": self._validate_id_required, "on_validation_error": "skip"},
        ) as dest:
            dest.write_bulk(
                [
                    {"id": 1, "name": "a"},
                    {"name": "no_id"},
                    {"id": 2, "name": "b"},
                ]
            )
        with open_iterable(str(output_file)) as src:
            rows = list(src)
        assert len(rows) == 2
        assert rows[0]["id"] == 1 and rows[1]["id"] == 2

    def test_validation_hook_on_write_sqlite(self, tmp_path):
        """Validation hook is applied when writing SQLite."""
        output_file = tmp_path / "out.db"
        with open_iterable(
            str(output_file),
            mode="w",
            iterableargs={
                "validation_hook": self._validate_id_required,
                "on_validation_error": "skip",
                "table": "t",
            },
        ) as dest:
            dest.write({"id": 1, "name": "a"})
            dest.write({"name": "no_id"})
            dest.write({"id": 2, "name": "b"})
        with open_iterable(str(output_file), iterableargs={"table": "t"}) as src:
            rows = list(src)
        assert len(rows) == 2
        # SQLite stores as TEXT
        assert str(rows[0]["id"]) == "1" and str(rows[1]["id"]) == "2"

    def test_validation_hook_on_write_topojson(self, tmp_path):
        """Validation hook is applied when writing TopoJSON; output is single Topology."""
        output_file = tmp_path / "out.topojson"
        with open_iterable(
            str(output_file),
            mode="w",
            iterableargs={"validation_hook": self._validate_id_required, "on_validation_error": "skip"},
        ) as dest:
            dest.write({"type": "Point", "coordinates": [0, 0], "id": 1})
            dest.write({"type": "Point", "coordinates": [1, 1]})  # no id - skipped
            dest.write({"type": "Point", "coordinates": [2, 2], "id": 2})
        with open_iterable(str(output_file)) as src:
            rows = list(src)
        # Single Topology written on close; read yields features
        assert len(rows) >= 1
        raw = output_file.read_text()
        assert raw.startswith('{"type": "Topology"')
        assert "objects" in raw
