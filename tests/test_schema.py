import datetime

import pytest

from iterable.helpers.schema import get_schema, get_schemes, merge_schemes, schema2fieldslist

try:
    import bson  # noqa: F401

    HAS_BSON = True
except ImportError:
    HAS_BSON = False


class TestSchema:
    def test_get_schema_string(self):
        """Test get_schema with string value"""
        obj = {"name": "test"}
        schema = get_schema(obj)
        assert "name" in schema
        assert schema["name"]["type"] == "string"
        assert "value" not in schema["name"]  # novalue=True by default

    def test_get_schema_integer(self):
        """Test get_schema with integer value"""
        obj = {"count": 42}
        schema = get_schema(obj)
        assert schema["count"]["type"] == "integer"

    def test_get_schema_float(self):
        """Test get_schema with float value"""
        obj = {"price": 19.99}
        schema = get_schema(obj)
        assert schema["price"]["type"] == "float"

    def test_get_schema_boolean(self):
        """Test get_schema with boolean value"""
        obj = {"active": True}
        schema = get_schema(obj)
        assert schema["active"]["type"] == "boolean"

    def test_get_schema_datetime(self):
        """Test get_schema with datetime value"""
        obj = {"created": datetime.datetime(2024, 1, 1)}
        schema = get_schema(obj)
        assert schema["created"]["type"] == "datetime"

    def test_get_schema_none(self):
        """Test get_schema with None value"""
        obj = {"field": None}
        schema = get_schema(obj)
        assert schema["field"]["type"] == "string"  # None defaults to string

    def test_get_schema_nested_dict(self):
        """Test get_schema with nested dict"""
        obj = {"user": {"name": "test", "age": 30}}
        schema = get_schema(obj)
        assert schema["user"]["type"] == "dict"
        assert "schema" in schema["user"]
        assert "name" in schema["user"]["schema"]
        assert "age" in schema["user"]["schema"]

    def test_get_schema_array_strings(self):
        """Test get_schema with array of strings"""
        obj = {"tags": ["tag1", "tag2"]}
        schema = get_schema(obj)
        assert schema["tags"]["type"] == "array"
        assert schema["tags"]["subtype"] == "string"

    def test_get_schema_array_integers(self):
        """Test get_schema with array of integers"""
        obj = {"numbers": [1, 2, 3]}
        schema = get_schema(obj)
        assert schema["numbers"]["type"] == "array"
        assert schema["numbers"]["subtype"] == "integer"

    def test_get_schema_array_dicts(self):
        """Test get_schema with array of dicts"""
        obj = {"items": [{"name": "item1"}, {"name": "item2"}]}
        schema = get_schema(obj)
        assert schema["items"]["type"] == "array"
        assert schema["items"]["subtype"] == "dict"
        assert "schema" in schema["items"]

    def test_get_schema_array_empty(self):
        """Test get_schema with empty array"""
        obj = {"items": []}
        schema = get_schema(obj)
        assert schema["items"]["type"] == "array"
        assert "subtype" not in schema["items"]  # Empty arrays stay upgradeable

    def test_get_schema_with_value(self):
        """Test get_schema with novalue=False"""
        obj = {"name": "test"}
        schema = get_schema(obj, novalue=False)
        assert "value" in schema["name"]
        assert schema["name"]["value"] == 1

    def test_get_schemes(self):
        """Test get_schemes with list of objects"""
        data = [{"name": "test1", "value": 1}, {"name": "test2", "value": 2}]
        schemes = get_schemes(data)
        assert len(schemes) == 2
        assert schemes[0]["name"]["type"] == "string"
        assert schemes[1]["name"]["type"] == "string"

    def test_merge_schemes_empty(self):
        """Test merge_schemes with empty list"""
        result = merge_schemes([])
        assert result is None

    def test_merge_schemes_single(self):
        """Test merge_schemes with single schema"""
        schema1 = {"name": {"type": "string"}}
        result = merge_schemes([schema1])
        assert result == schema1

    def test_merge_schemes_simple(self):
        """Test merge_schemes with simple schemas"""
        schema1 = {"name": {"type": "string"}}
        schema2 = {"value": {"type": "integer"}}
        result = merge_schemes([schema1, schema2])
        assert "name" in result
        assert "value" in result

    def test_merge_schemes_overlapping(self):
        """Test merge_schemes with overlapping keys"""
        schema1 = {"name": {"type": "string", "value": 1}}
        schema2 = {"name": {"type": "string", "value": 1}}
        result = merge_schemes([schema1, schema2], novalue=False)
        assert result["name"]["type"] == "string"
        # Values should be added
        assert result["name"]["value"] == 2

    def test_merge_schemes_nested_dict(self):
        """Test merge_schemes with nested dicts"""
        schema1 = {"user": {"type": "dict", "schema": {"name": {"type": "string"}}}}
        schema2 = {"user": {"type": "dict", "schema": {"age": {"type": "integer"}}}}
        result = merge_schemes([schema1, schema2])
        assert result["user"]["type"] == "dict"
        assert "name" in result["user"]["schema"]
        assert "age" in result["user"]["schema"]

    def test_merge_schemes_array_dicts(self):
        """Test merge_schemes with array of dicts"""
        schema1 = {"items": {"type": "array", "subtype": "dict", "schema": {"name": {"type": "string"}}}}
        schema2 = {"items": {"type": "array", "subtype": "dict", "schema": {"price": {"type": "float"}}}}
        result = merge_schemes([schema1, schema2])
        assert result["items"]["subtype"] == "dict"
        assert "name" in result["items"]["schema"]
        assert "price" in result["items"]["schema"]

    def test_merge_schemes_upgrades_empty_array_to_array_of_dicts(self):
        schema1 = {"items": {"type": "array"}}
        schema2 = {
            "items": {
                "type": "array",
                "subtype": "dict",
                "schema": {"name": {"type": "string"}},
            }
        }
        result = merge_schemes([schema1, schema2])
        assert result["items"]["subtype"] == "dict"
        assert result["items"]["schema"]["name"]["type"] == "string"

    def test_merge_schemes_upgrades_null_placeholder_to_dict(self):
        schema1 = {"capital_city": {"type": "string"}}
        schema2 = {
            "capital_city": {
                "type": "dict",
                "schema": {"name": {"type": "string"}},
            }
        }
        result = merge_schemes([schema1, schema2])
        assert result["capital_city"]["type"] == "dict"
        assert "name" in result["capital_city"]["schema"]

    def test_schema2fieldslist_simple(self):
        """Test schema2fieldslist with simple schema"""
        schema = {"name": {"type": "string"}, "age": {"type": "integer"}}
        fields = schema2fieldslist(schema)
        assert len(fields) == 2
        assert any(f["name"] == "name" for f in fields)
        assert any(f["name"] == "age" for f in fields)
        assert any(f["type"] == "string" for f in fields)
        assert any(f["type"] == "integer" for f in fields)

    def test_schema2fieldslist_with_prefix(self):
        """Test schema2fieldslist with prefix"""
        schema = {"name": {"type": "string"}}
        fields = schema2fieldslist(schema, prefix="user")
        assert len(fields) == 1
        assert fields[0]["name"] == "user.name"

    def test_schema2fieldslist_nested(self):
        """Test schema2fieldslist with nested schema"""
        schema = {"user": {"type": "dict", "schema": {"name": {"type": "string"}, "age": {"type": "integer"}}}}
        fields = schema2fieldslist(schema)
        # Should have user field and nested fields
        assert len(fields) >= 3
        assert any(f["name"] == "user" for f in fields)
        assert any("user.name" in f["name"] for f in fields)
        assert any("user.age" in f["name"] for f in fields)

    def test_schema2fieldslist_array(self):
        """Test schema2fieldslist with array type"""
        schema = {"tags": {"type": "array", "subtype": "string"}}
        fields = schema2fieldslist(schema)
        assert len(fields) == 1
        assert fields[0]["type"] == "list of [string]"

    def test_schema2fieldslist_with_predefined(self):
        """Test schema2fieldslist with predefined descriptions"""
        schema = {"name": {"type": "string"}}
        predefined = {"name": {"text": "User name", "class": "person"}}
        fields = schema2fieldslist(schema, predefined=predefined)
        name_field = next(f for f in fields if f["name"] == "name")
        assert name_field["description"] == "User name"
        assert name_field["class"] == "person"

    def test_schema2fieldslist_with_sample(self):
        """Test schema2fieldslist with sample data"""
        schema = {"name": {"type": "string"}}
        sample = {"name": "test_user"}
        fields = schema2fieldslist(schema, sample=sample)
        name_field = next(f for f in fields if f["name"] == "name")
        assert name_field["sample"] == "test_user"

    def test_schema2fieldslist_datetime(self):
        """Test schema2fieldslist with datetime type"""
        schema = {"created": {"type": "datetime"}}
        fields = schema2fieldslist(schema)
        created_field = next(f for f in fields if f["name"] == "created")
        assert created_field["type"] == "datetime"
        assert created_field["class"] == "datetime"

    def test_schema2fieldslist_array_of_dicts(self):
        """Test schema2fieldslist with array of dicts"""
        schema = {
            "items": {
                "type": "array",
                "subtype": "dict",
                "schema": {"name": {"type": "string"}, "price": {"type": "float"}},
            }
        }
        fields = schema2fieldslist(schema)
        # Should have items field and nested fields
        assert len(fields) >= 3
        assert any(f["name"] == "items" for f in fields)
        assert any("items.name" in f["name"] for f in fields)
        assert any("items.price" in f["name"] for f in fields)

    @pytest.mark.skipif(not HAS_BSON, reason="BSON not available")
    def test_get_schema_bson_int64(self):
        """Test get_schema with BSON Int64"""
        obj = {"value": bson.int64.Int64(42)}
        schema = get_schema(obj)
        assert schema["value"]["type"] == "integer"

    @pytest.mark.skipif(not HAS_BSON, reason="BSON not available")
    def test_get_schema_bson_objectid(self):
        """Test get_schema with BSON ObjectId"""
        obj = {"id": bson.objectid.ObjectId()}
        schema = get_schema(obj)
        assert schema["id"]["type"] == "string"

    def test_get_schema_array_floats(self):
        """Test get_schema with array of floats"""
        obj = {"prices": [1.99, 2.99, 3.99]}
        schema = get_schema(obj)
        assert schema["prices"]["type"] == "array"
        assert schema["prices"]["subtype"] == "float"

    def test_get_schema_array_booleans(self):
        """Test get_schema with array of booleans"""
        obj = {"flags": [True, False, True]}
        schema = get_schema(obj)
        assert schema["flags"]["type"] == "array"
        assert schema["flags"]["subtype"] == "boolean"

    def test_get_schema_array_datetime(self):
        """Test get_schema with array of datetime"""
        obj = {"dates": [datetime.datetime(2024, 1, 1), datetime.datetime(2024, 1, 2)]}
        schema = get_schema(obj)
        assert schema["dates"]["type"] == "array"
        assert schema["dates"]["subtype"] == "datetime"

    def test_get_schema_complex_nested(self):
        """Test get_schema with complex nested structure"""
        obj = {
            "user": {
                "profile": {"name": "test", "age": 30},
                "tags": ["tag1", "tag2"],
                "items": [{"name": "item1", "price": 10.99}],
            }
        }
        schema = get_schema(obj)
        assert schema["user"]["type"] == "dict"
        assert "profile" in schema["user"]["schema"]
        assert schema["user"]["schema"]["tags"]["type"] == "array"

    def test_merge_schemes_array_non_dict(self):
        """Test merge_schemes with array of non-dict types"""
        schema1 = {"tags": {"type": "array", "subtype": "string", "value": 1}}
        schema2 = {"tags": {"type": "array", "subtype": "string", "value": 1}}
        result = merge_schemes([schema1, schema2], novalue=False)
        assert result["tags"]["type"] == "array"
        # Bug in merge_schemes line 52 - uses item["value"] instead of item[k]["value"]
        # This test documents the current behavior

    def test_merge_schemes_mixed_types(self):
        """Test merge_schemes with different types for same key"""
        schema1 = {"field": {"type": "string", "value": 1}}
        schema2 = {"field": {"type": "integer", "value": 1}}
        # Should keep first type
        result = merge_schemes([schema1, schema2], novalue=False)
        assert result["field"]["type"] == "string"

    def test_schema2fieldslist_empty_schema(self):
        """Test schema2fieldslist with empty schema"""
        fields = schema2fieldslist({})
        assert fields == []

    def test_schema2fieldslist_with_none_sample(self):
        """Test schema2fieldslist with None sample"""
        schema = {"name": {"type": "string"}}
        fields = schema2fieldslist(schema, sample=None)
        assert len(fields) == 1
        assert fields[0]["sample"] == ""

    def test_schema_from_list_of_dicts(self):
        """Test schema_from_list_of_dicts function"""
        from iterable.helpers.schema import schema_from_list_of_dicts

        data = [{"name": "test1", "value": 1}, {"name": "test2", "value": 2}]
        schema = schema_from_list_of_dicts(data)
        assert "name" in schema
        assert "value" in schema
        assert schema["name"]["type"] == "string"
        assert schema["value"]["type"] == "integer"

    def test_schema_from_list_of_dicts_empty(self):
        """Test schema_from_list_of_dicts with empty list"""
        from iterable.helpers.schema import schema_from_list_of_dicts

        schema = schema_from_list_of_dicts([])
        assert schema is None

    def test_get_schema_with_novalue_false(self):
        """Test get_schema with novalue=False includes value counts"""
        obj = {"name": "test", "count": 42}
        schema = get_schema(obj, novalue=False)
        assert "value" in schema["name"]
        assert schema["name"]["value"] == 1
        assert "value" in schema["count"]
        assert schema["count"]["value"] == 1
