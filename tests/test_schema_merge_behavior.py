"""Behavior-pinning tests for merge_schemes (complexity refactor).

Pins the observable behavior of ``iterable.helpers.schema.merge_schemes``
before/after the behavior-preserving decomposition: in-place mutation of the
first schema, key union order, ``novalue`` handling, weak-placeholder upgrades
(null strings / empty arrays upgraded to dict / array-of-dict shapes), and the
recursive dict/array schema merge branches.
"""

from iterable.helpers.schema import merge_schemes


class TestResultShape:
    def test_empty_list_returns_none(self):
        assert merge_schemes([]) is None

    def test_single_schema_returned_by_identity(self):
        """The first schema object is mutated in place and returned."""
        schema = {"a": {"type": "integer", "value": 1}}
        result = merge_schemes([schema])
        assert result is schema

    def test_disjoint_keys_union_in_order(self):
        left = {"x": {"type": "string", "value": 1}}
        right = {"y": {"type": "float", "value": 1}, "z": {"type": "boolean", "value": 1}}
        result = merge_schemes([left, right])
        assert list(result.keys()) == ["x", "y", "z"]
        assert result["y"] == {"type": "float", "value": 1}
        assert result["z"] == {"type": "boolean", "value": 1}

    def test_non_dict_entries_are_skipped(self):
        """Non-dict left/right values are left untouched (no merge attempted)."""
        left = {"k": "plainstring"}
        assert merge_schemes([left, {"k": {"type": "integer", "value": 1}}]) == {"k": "plainstring"}
        left = {"k": {"type": "integer", "value": 1}}
        assert merge_schemes([left, {"k": 42}]) == {"k": {"type": "integer", "value": 1}}


class TestScalarMerging:
    def test_novalue_true_keeps_left_value(self):
        left = {"a": {"type": "integer", "value": 2}}
        right = {"a": {"type": "integer", "value": 3}}
        assert merge_schemes([left, right]) == {"a": {"type": "integer", "value": 2}}

    def test_novalue_false_sums_values(self):
        left = {"a": {"type": "integer", "value": 2}}
        right = {"a": {"type": "integer", "value": 3}}
        assert merge_schemes([left, right], novalue=False) == {"a": {"type": "integer", "value": 5}}

    def test_novalue_false_sums_each_scalar_type(self):
        for stype in ("integer", "float", "string", "datetime"):
            left = {"a": {"type": stype, "value": 1}}
            right = {"a": {"type": stype, "value": 4}}
            result = merge_schemes([left, right], novalue=False)
            assert result == {"a": {"type": stype, "value": 5}}

    def test_string_left_does_not_upgrade_to_scalar(self):
        """A weak string placeholder only upgrades to dict/array shapes; the
        scalar branch runs instead and sums values when novalue=False."""
        left = {"k": {"type": "string", "value": 1}}
        right = {"k": {"type": "integer", "value": 5}}
        assert merge_schemes([left, right], novalue=False) == {"k": {"type": "string", "value": 6}}


class TestDictMerging:
    def test_recursive_schema_merge(self):
        left = {"k": {"type": "dict", "value": 1, "schema": {"a": {"type": "integer", "value": 1}}}}
        right = {"k": {"type": "dict", "value": 2, "schema": {"b": {"type": "string", "value": 1}}}}
        result = merge_schemes([left, right], novalue=False)
        assert result["k"]["value"] == 3
        assert result["k"]["schema"] == {"a": {"type": "integer", "value": 1}, "b": {"type": "string", "value": 1}}

    def test_right_schema_adopted_when_left_lacks_it(self):
        left = {"k": {"type": "dict", "value": 1}}
        right = {"k": {"type": "dict", "value": 1, "schema": {"n": {"type": "integer", "value": 1}}}}
        result = merge_schemes([left, right], novalue=False)
        assert result["k"]["schema"] == {"n": {"type": "integer", "value": 1}}
        assert result["k"]["value"] == 2


class TestArrayMerging:
    def test_array_of_dicts_recursive_merge(self):
        left = {"k": {"type": "array", "subtype": "dict", "schema": {"a": {"type": "integer", "value": 1}}, "value": 1}}
        right = {"k": {"type": "array", "subtype": "dict", "schema": {"b": {"type": "string", "value": 1}}, "value": 2}}
        result = merge_schemes([left, right], novalue=False)
        assert result["k"]["value"] == 3
        assert result["k"]["schema"] == {"a": {"type": "integer", "value": 1}, "b": {"type": "string", "value": 1}}

    def test_left_array_adopts_right_dict_subtype(self):
        """Left array without dict subtype adopts the right schema/subtype."""
        left = {"k": {"type": "array", "value": 1}}
        right = {"k": {"type": "array", "subtype": "dict", "schema": {"c": {"type": "string", "value": 1}}, "value": 1}}
        result = merge_schemes([left, right])
        assert result["k"]["subtype"] == "dict"
        assert result["k"]["schema"] == {"c": {"type": "string", "value": 1}}

    def test_left_dict_subtype_merges_right_schema_without_subtype(self):
        """The ``elif`` branch: left is already array-of-dict and right carries
        a schema (without a dict subtype) — schemas merge recursively."""
        left = {"k": {"type": "array", "subtype": "dict", "schema": {"a": {"type": "integer", "value": 1}}, "value": 1}}
        right = {"k": {"type": "array", "schema": {"b": {"type": "string", "value": 1}}, "value": 2}}
        result = merge_schemes([left, right], novalue=False)
        assert result["k"]["schema"] == {"a": {"type": "integer", "value": 1}, "b": {"type": "string", "value": 1}}
        assert result["k"]["value"] == 3


class TestWeakPlaceholderUpgrades:
    def test_null_placeholder_upgrades_to_dict(self):
        """A None-derived string placeholder is replaced by the dict shape."""
        left = {"k": {"type": "string", "value": 1}}
        right = {"k": {"type": "dict", "value": 1, "schema": {"n": {"type": "integer", "value": 1}}}}
        result = merge_schemes([left, right], novalue=False)
        assert result["k"]["type"] == "dict"
        assert result["k"]["schema"] == {"n": {"type": "integer", "value": 1}}
        # Upgrade path sums left+right values when novalue=False.
        assert result["k"]["value"] == 2

    def test_upgrade_keeps_right_value_when_novalue(self):
        left = {"k": {"type": "string", "value": 1}}
        right = {"k": {"type": "dict", "schema": {"n": {"type": "integer", "value": 1}}}}
        result = merge_schemes([left, right])
        assert result["k"]["type"] == "dict"
        assert "value" not in result["k"]

    def test_empty_array_upgrades_to_array_of_dicts(self):
        left = {"k": {"type": "array", "value": 1}}
        right = {"k": {"type": "array", "subtype": "dict", "schema": {"c": {"type": "string", "value": 1}}, "value": 1}}
        result = merge_schemes([left, right], novalue=False)
        assert result["k"]["subtype"] == "dict"
        assert result["k"]["schema"] == {"c": {"type": "string", "value": 1}}
        assert result["k"]["value"] == 2

    def test_array_subtype_upgrade_from_none_subtype(self):
        """Left array with explicit ``subtype: None`` upgrades to right's subtype."""
        left = {"k": {"type": "array", "subtype": None, "value": 1}}
        right = {"k": {"type": "array", "subtype": "string", "value": 1}}
        result = merge_schemes([left, right])
        assert result["k"]["subtype"] == "string"
