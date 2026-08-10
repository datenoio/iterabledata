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

    def test_infer_flatten_nested_capital_city(self):
        """Nested dict fields unfold to dotted paths when requested."""
        rows = [
            {
                "country": "FR",
                "capital_city": {"name": "Paris", "lat": 48.8566, "lng": 2.3522},
            },
            {
                "country": "JP",
                "capital_city": {"name": "Tokyo", "lat": 35.6762, "lng": 139.6503},
            },
        ]
        sch = schema.infer(rows, flatten_nested=True)
        fields = sch["fields"]
        assert "capital_city" in fields
        assert fields["capital_city"]["type"] == "dict"
        assert "capital_city.name" in fields
        assert fields["capital_city.name"]["type"] == "string"
        assert "capital_city.lat" in fields
        assert fields["capital_city.lat"]["type"] == "float"
        assert "capital_city.lng" in fields
        assert fields["capital_city.lng"]["type"] == "float"
        assert fields["capital_city.name"]["sample_values"][0] == "Paris"

    def test_infer_without_flatten_keeps_parent_only(self):
        rows = [{"capital_city": {"name": "Paris", "lat": 48.8}}]
        sch = schema.infer(rows)
        assert "capital_city" in sch["fields"]
        assert "capital_city.name" not in sch["fields"]

    def test_infer_flatten_array_of_dicts(self):
        rows = [
            {
                "id": 1,
                "tags": [{"code": "a", "label": "Alpha"}, {"code": "b", "label": "Beta"}],
            }
        ]
        sch = schema.infer(rows, flatten_nested=True)
        assert "tags" in sch["fields"]
        assert sch["fields"]["tags"]["type"] == "array"
        assert "tags.code" in sch["fields"]
        assert "tags.label" in sch["fields"]
        assert sch["fields"]["tags.code"]["sample_values"][0] == ["a", "b"]

    def test_infer_flatten_array_upgrades_after_empty_first_rows(self):
        rows = [
            {"id": 1, "items": []},
            {"id": 2, "items": None},
            {"id": 3, "items": [{"name": "a", "score": 1}]},
            {"id": 4, "items": [{"name": "b", "score": 2}, {"name": "c", "score": 3}]},
        ]
        sch = schema.infer(rows, flatten_nested=True)
        assert sch["fields"]["items"]["type"] == "array"
        assert sch["fields"]["items"].get("subtype") == "dict"
        assert "items.name" in sch["fields"]
        assert "items.score" in sch["fields"]
        assert sch["fields"]["items.name"]["type"] == "string"
        assert sch["fields"]["items.score"]["type"] == "integer"

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
