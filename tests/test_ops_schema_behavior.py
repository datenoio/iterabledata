"""Behavior-pinning tests for iterable.ops.schema.infer (complexity refactor).

Pins the observable behavior of ``schema.infer`` before/after the
behavior-preserving decomposition: type detection, nullability, sample values,
constraints (min/max, lengths, enums), nested flattening, and edge cases.
"""

from iterable.ops import schema


class TestBasicInference:
    def test_scalar_types(self):
        rows = [{"i": 1, "f": 1.5, "s": "x", "b": True}]
        result = schema.infer(rows)
        assert result["fields"]["i"]["type"] == "integer"
        assert result["fields"]["f"]["type"] == "float"
        assert result["fields"]["s"]["type"] == "string"
        assert result["fields"]["b"]["type"] == "boolean"

    def test_subtype_preserved_for_arrays(self):
        rows = [{"arr": [1, 2, 3]}]
        result = schema.infer(rows)
        assert result["fields"]["arr"]["type"] == "array"
        assert result["fields"]["arr"]["subtype"] == "integer"

    def test_no_subtype_key_when_absent(self):
        rows = [{"i": 1}]
        result = schema.infer(rows)
        assert "subtype" not in result["fields"]["i"]

    def test_empty_iterable(self):
        result = schema.infer(iter([]))
        assert result == {"fields": {}, "constraints": {}}

    def test_constraints_key_only_when_requested(self):
        rows = [{"i": 1}]
        assert "constraints" not in schema.infer(rows)
        assert "constraints" in schema.infer(rows, detect_constraints=True)

    def test_sample_size_limits_rows_considered(self):
        rows = [{"i": i} for i in range(20)]
        rows.append({"i": "late-string"})  # beyond sample window
        result = schema.infer(rows, sample_size=5)
        assert result["fields"]["i"]["type"] == "integer"

    def test_sample_values_capped_at_five(self):
        rows = [{"i": i} for i in range(10)]
        result = schema.infer(rows)
        assert result["fields"]["i"]["sample_values"] == [0, 1, 2, 3, 4]

    def test_file_path_input(self):
        result = schema.infer("fixtures/2cols6rows.csv")
        assert set(result["fields"].keys()) != set()


class TestNullability:
    def test_null_value_makes_nullable(self):
        rows = [{"a": 1}, {"a": None}]
        result = schema.infer(rows)
        assert result["fields"]["a"]["nullable"] is True

    def test_missing_field_makes_nullable(self):
        rows = [{"a": 1, "b": 2}, {"a": 3}]
        result = schema.infer(rows)
        assert result["fields"]["b"]["nullable"] is True
        assert result["fields"]["a"]["nullable"] is False

    def test_all_present_non_null_not_nullable(self):
        rows = [{"a": 1}, {"a": 2}, {"a": 3}]
        result = schema.infer(rows)
        assert result["fields"]["a"]["nullable"] is False


class TestConstraints:
    def test_numeric_min_max(self):
        rows = [{"n": n} for n in [3, 1, 4, 1, 5, 9, 2, 6]]
        result = schema.infer(rows, detect_constraints=True)
        assert result["constraints"]["n"]["min"] == 1
        assert result["constraints"]["n"]["max"] == 9

    def test_string_length_constraints(self):
        rows = [{"s": s} for s in ["a", "bb", "ccc"]]
        result = schema.infer(rows, detect_constraints=True)
        assert result["constraints"]["s"]["min_length"] == 1
        assert result["constraints"]["s"]["max_length"] == 3

    def test_enum_detection_for_low_cardinality(self):
        """<=10 distinct values across >5 non-null rows yields possible_values."""
        rows = [{"status": s} for s in ["a", "b", "a", "c", "b", "a", "c"]]
        result = schema.infer(rows, detect_constraints=True)
        assert set(result["constraints"]["status"]["possible_values"]) == {"a", "b", "c"}

    def test_no_enum_for_few_rows(self):
        """possible_values requires more than 5 non-null values."""
        rows = [{"status": s} for s in ["a", "b", "a", "c", "b"]]
        result = schema.infer(rows, detect_constraints=True)
        assert "possible_values" not in result["constraints"].get("status", {})

    def test_no_enum_for_high_cardinality(self):
        rows = [{"s": f"value-{i}"} for i in range(20)]
        result = schema.infer(rows, detect_constraints=True)
        assert "possible_values" not in result["constraints"].get("s", {})

    def test_field_without_constraints_absent(self):
        """Fields producing no constraints do not appear in the constraints dict."""
        rows = [{"b": True} for _ in range(3)]
        result = schema.infer(rows, detect_constraints=True)
        assert result["constraints"].get("b") is None or "min" not in result["constraints"].get("b", {})


class TestFlattenNested:
    def test_flatten_nested_dotted_paths(self):
        rows = [
            {"name": "x", "capital_city": {"lat": 1.0, "lng": 2.0}},
            {"name": "y", "capital_city": {"lat": 3.0, "lng": 4.0}},
        ]
        result = schema.infer(rows, flatten_nested=True)
        assert "capital_city.lat" in result["fields"]
        assert "capital_city.lng" in result["fields"]
        assert result["fields"]["capital_city.lat"]["type"] == "float"

    def test_flatten_nested_keeps_parents_by_default(self):
        rows = [{"d": {"a": 1}}]
        result = schema.infer(rows, flatten_nested=True)
        assert "d" in result["fields"]
        assert result["fields"]["d"]["type"] == "dict"

    def test_flatten_nested_can_drop_parents(self):
        rows = [{"d": {"a": 1}}]
        result = schema.infer(rows, flatten_nested=True, keep_nested_parents=False)
        assert "d" not in result["fields"]
        assert "d.a" in result["fields"]

    def test_flatten_nested_nullable_when_path_missing(self):
        rows = [{"d": {"a": 1}}, {"other": True}]
        result = schema.infer(rows, flatten_nested=True)
        assert result["fields"]["d.a"]["nullable"] is True

    def test_flatten_nested_constraints_on_children(self):
        rows = [{"d": {"n": i}} for i in range(1, 8)]
        result = schema.infer(rows, flatten_nested=True, detect_constraints=True)
        assert result["constraints"]["d.n"]["min"] == 1
        assert result["constraints"]["d.n"]["max"] == 7

    def test_array_of_scalars_exploded_for_constraints(self):
        """Scalar-list values under a dotted path contribute each element."""
        rows = [
            {"langs": {"code": ["en", "fr"]}},
            {"langs": {"code": ["de"]}},
        ]
        result = schema.infer(rows, flatten_nested=True, detect_constraints=True)
        field = result["fields"]["langs.code"]
        assert field["type"] == "array"
        # Nullability from present (non-empty) values
        assert field["nullable"] is False
