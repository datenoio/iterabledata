"""Tests for nested schema / row projection helpers."""

from iterable.helpers.nested import (
    nested_field_value,
    project_row_nested,
    unfold_nested_schema_fields,
)


def test_unfold_nested_schema_fields_keeps_parents():
    deep = {
        "capital_city": {
            "type": "dict",
            "schema": {
                "name": {"type": "string"},
                "lat": {"type": "float"},
            },
        }
    }
    fields = dict(unfold_nested_schema_fields(deep, keep_parents=True))
    assert fields["capital_city"]["type"] == "dict"
    assert fields["capital_city.name"]["type"] == "string"
    assert fields["capital_city.lat"]["type"] == "float"


def test_project_row_nested_capital_city():
    row = {"id": 1, "capital_city": {"name": "Paris", "lat": 48.8}}
    projected = project_row_nested(row)
    assert projected["id"] == 1
    assert projected["capital_city"] == {"name": "Paris", "lat": 48.8}
    assert projected["capital_city.name"] == "Paris"
    assert projected["capital_city.lat"] == 48.8


def test_project_row_nested_array_of_dicts_collects_all_elements():
    row = {
        "languages": [
            {"code": "rus", "name": "Russian"},
            {"code": "tgk", "name": "Tajik"},
        ]
    }
    projected = project_row_nested(row)
    assert projected["languages.code"] == ["rus", "tgk"]
    assert projected["languages.name"] == ["Russian", "Tajik"]


def test_nested_field_value():
    row = {"capital_city": {"name": "Paris"}}
    assert nested_field_value(row, "capital_city.name") == "Paris"
    assert nested_field_value(row, "missing") is None
    row = {"languages": [{"code": "en"}, {"code": "fr"}]}
    assert nested_field_value(row, "languages.code") == ["en", "fr"]
