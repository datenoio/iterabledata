"""
Tests for ops.schema module.
"""

from iterable.ops import schema


class TestSchema:
    def test_infer_basic(self):
        """Test basic schema inference."""
        rows = [
            {"name": "John", "age": 30, "active": True},
            {"name": "Jane", "age": 25, "active": False},
        ]
        sch = schema.infer(rows)
        assert "fields" in sch
        assert "name" in sch["fields"]
        assert "age" in sch["fields"]
        assert "active" in sch["fields"]
        assert sch["fields"]["name"]["type"] == "string"
        assert sch["fields"]["age"]["type"] == "integer"
        assert sch["fields"]["active"]["type"] == "boolean"

    def test_infer_with_constraints(self):
        """Test schema inference with constraints."""
        rows = [
            {"price": 10.0},
            {"price": 20.0},
            {"price": 30.0},
        ]
        sch = schema.infer(rows, detect_constraints=True)
        assert "constraints" in sch
        assert "price" in sch["constraints"]
        assert "min" in sch["constraints"]["price"]
        assert "max" in sch["constraints"]["price"]
        assert sch["constraints"]["price"]["min"] == 10.0
        assert sch["constraints"]["price"]["max"] == 30.0

    def test_infer_with_nulls(self):
        """Test schema inference with null values."""
        rows = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": None},
        ]
        sch = schema.infer(rows)
        assert sch["fields"]["age"]["nullable"] is True
        assert sch["fields"]["name"]["nullable"] is False

    def test_to_jsonschema(self):
        """Test JSON Schema conversion."""
        sch = {
            "fields": {
                "name": {"type": "string", "nullable": False},
                "age": {"type": "integer", "nullable": True},
            }
        }
        json_schema = schema.to_jsonschema(sch)
        assert json_schema["type"] == "object"
        assert "properties" in json_schema
        assert "name" in json_schema["properties"]
        assert json_schema["properties"]["name"]["type"] == "string"
        assert "name" in json_schema["required"]

    def test_to_jsonschema_with_constraints(self):
        """Test JSON Schema with constraints."""
        sch = {
            "fields": {
                "price": {"type": "float", "nullable": False},
            },
            "constraints": {
                "price": {"min": 10.0, "max": 100.0},
            },
        }
        json_schema = schema.to_jsonschema(sch)
        assert json_schema["properties"]["price"]["minimum"] == 10.0
        assert json_schema["properties"]["price"]["maximum"] == 100.0

    def test_to_yaml(self):
        """Test YAML conversion."""
        sch = {
            "fields": {
                "name": {"type": "string", "nullable": False},
            }
        }
        yaml_str = schema.to_yaml(sch)
        assert isinstance(yaml_str, str)
        assert "name" in yaml_str

    def test_to_cerberus(self):
        """Test Cerberus conversion."""
        sch = {
            "fields": {
                "name": {"type": "string", "nullable": False},
                "age": {"type": "integer", "nullable": True},
            }
        }
        cerberus_schema = schema.to_cerberus(sch)
        assert "name" in cerberus_schema
        assert cerberus_schema["name"]["type"] == "string"
        assert cerberus_schema["name"]["required"] is True
        assert cerberus_schema["age"]["required"] is False

    def test_to_avro(self):
        """Test Avro conversion."""
        sch = {
            "fields": {
                "name": {"type": "string", "nullable": False},
                "age": {"type": "integer", "nullable": True},
            }
        }
        avro_schema = schema.to_avro(sch)
        assert avro_schema["type"] == "record"
        assert "fields" in avro_schema
        assert len(avro_schema["fields"]) == 2

    def test_to_parquet_metadata(self):
        """Test Parquet metadata conversion."""
        sch = {
            "fields": {
                "name": {"type": "string", "nullable": False},
                "age": {"type": "integer", "nullable": True},
            }
        }
        parquet_meta = schema.to_parquet_metadata(sch)
        assert "fields" in parquet_meta
        assert len(parquet_meta["fields"]) == 2

    def test_validate_against_schema(self):
        """Test validating data against schema."""
        sch = {
            "fields": {
                "name": {"type": "string", "nullable": False},
                "age": {"type": "integer", "nullable": True},
            }
        }
        rows = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": "invalid"},  # Wrong type
            {"age": 25},  # Missing required field
        ]
        result = schema.validate(rows, sch)
        assert "valid_rows" in result
        assert "invalid_rows" in result
        assert "stats" in result
        assert len(result["valid_rows"]) == 1
        assert len(result["invalid_rows"]) == 2

    def test_validate_strict_mode(self):
        """Test strict schema validation."""
        sch = {
            "fields": {
                "name": {"type": "string", "nullable": False},
            }
        }
        rows = [
            {"name": "John"},
            {"name": "Jane", "extra": "field"},  # Extra field
        ]
        result = schema.validate(rows, sch, strict=True)
        assert len(result["invalid_rows"]) >= 1  # Second row has extra field
