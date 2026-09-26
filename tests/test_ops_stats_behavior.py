"""Behavior-pinning tests for ops.stats.compute (complexity refactor).

Pins the observable behavior of ``iterable.ops.stats.compute`` before/after the
behavior-preserving decomposition: per-field accumulation (count/null/unique),
numeric statistics (min/max/mean/median/stddev), string length statistics,
top_values, dictionary-field detection (explicit and env-var thresholds), and
the flatten_nested projection mode including scalar-list explosion and
missing-row null accounting.
"""

import pytest

from iterable.ops import stats


class TestBasicAccumulation:
    def test_basic_counts(self):
        summary = stats.compute([{"value": 1, "name": "a"}, {"value": 2, "name": "b"}, {"value": 3, "name": "c"}])
        assert summary["value"]["count"] == 3
        assert summary["value"]["null_count"] == 0
        assert summary["value"]["null_fraction"] == 0.0
        assert summary["value"]["unique_count"] == 3
        assert summary["value"]["is_dictionary"] is False

    def test_nulls_counted(self):
        summary = stats.compute([{"value": 1}, {"value": None}, {"value": 3}])
        assert summary["value"]["count"] == 2
        assert summary["value"]["null_count"] == 1
        assert summary["value"]["null_fraction"] == pytest.approx(1 / 3)

    def test_all_null_field(self):
        """An all-null field has count 0, null_fraction 1.0 and no min/max keys."""
        summary = stats.compute([{"a": None}, {"a": None}])
        field = summary["a"]
        assert field["count"] == 0
        assert field["null_count"] == 2
        assert field["null_fraction"] == 1.0
        assert field["unique_count"] == 0
        assert field["is_dictionary"] is False
        assert "min" not in field
        assert "stddev" not in field

    def test_empty_iterable(self):
        assert stats.compute([]) == {}

    def test_unhashable_values_counted_unique_via_repr(self):
        """Lists/dicts are deduplicated through hashable_repr."""
        summary = stats.compute([{"v": [1, 2]}, {"v": [1, 2]}, {"v": {"a": 1}}])
        assert summary["v"]["count"] == 3
        assert summary["v"]["unique_count"] == 2

    def test_numeric_strings_not_numeric(self):
        summary = stats.compute([{"v": "1"}, {"v": "2"}])
        assert "min" not in summary["v"]
        assert summary["v"]["min_length"] == 1

    def test_accepts_file_path_string(self):
        summary = stats.compute("fixtures/2cols6rows.csv")
        assert isinstance(summary, dict)
        assert len(summary) > 0


class TestNumericStats:
    def test_min_max_mean(self):
        summary = stats.compute([{"value": 1}, {"value": 2}, {"value": 3}])
        field = summary["value"]
        assert field["min"] == 1
        assert field["max"] == 3
        assert field["mean"] == 2.0

    def test_odd_median(self):
        summary = stats.compute([{"v": 1}, {"v": 2}, {"v": 10}])
        assert summary["v"]["median"] == 2

    def test_even_median(self):
        summary = stats.compute([{"v": 1}, {"v": 2}, {"v": 3}, {"v": 4}])
        assert summary["v"]["median"] == 2.5

    def test_single_value_stddev_zero(self):
        summary = stats.compute([{"v": 5}])
        assert summary["v"]["stddev"] == 0.0
        assert summary["v"]["median"] == 5

    def test_stddev_population_formula(self):
        summary = stats.compute([{"v": 1}, {"v": 2}, {"v": 3}])
        assert summary["v"]["stddev"] == pytest.approx(0.816496580927726)

    def test_bool_values_treated_as_numeric(self):
        """bool is an int subclass, so booleans land in numeric stats."""
        summary = stats.compute([{"v": True}, {"v": False}, {"v": True}])
        field = summary["v"]
        assert field["min"] is False
        assert field["max"] is True
        assert field["mean"] == pytest.approx(2 / 3)
        assert field["unique_count"] == 2

    def test_mixed_numeric_and_string(self):
        """Numeric stats use only numeric values; string stats only strings."""
        summary = stats.compute([{"v": 1}, {"v": "x"}, {"v": 2.5}])
        field = summary["v"]
        assert field["min"] == 1
        assert field["max"] == 2.5
        assert field["mean"] == 1.75
        assert field["min_length"] == 1


class TestStringStats:
    def test_length_stats(self):
        summary = stats.compute([{"s": "ab"}, {"s": "cdef"}, {"s": "g"}])
        field = summary["s"]
        assert field["min_length"] == 1
        assert field["max_length"] == 4
        assert field["avg_length"] == pytest.approx(7 / 3)


class TestTopValues:
    def test_top_values_limited(self):
        rows = [{"s": "a"}, {"s": "b"}, {"s": "a"}, {"s": "c"}, {"s": "a"}]
        summary = stats.compute(rows, include_top_values=True, top_n=2)
        assert summary["s"]["top_values"] == [{"value": "a", "count": 3}, {"value": "b", "count": 1}]

    def test_top_values_absent_by_default(self):
        summary = stats.compute([{"s": "a"}])
        assert "top_values" not in summary["s"]

    def test_top_values_absent_for_all_null_field(self):
        """values is empty for an all-null field, so no top_values key is emitted."""
        summary = stats.compute([{"a": None}, {"a": None}], include_top_values=True)
        assert "top_values" not in summary["a"]

    def test_top_values_unhashable_use_hashable_key(self):
        summary = stats.compute([{"v": [1]}, {"v": [1]}, {"v": [2]}], include_top_values=True, top_n=5)
        assert summary["v"]["top_values"] == [{"value": "[1]", "count": 2}, {"value": "[2]", "count": 1}]


class TestDictionaryThreshold:
    def test_low_cardinality_above_default_threshold_not_dictionary(self):
        rows = [{"s": "a"}, {"s": "b"}] * 5
        summary = stats.compute(rows)
        assert summary["s"]["unique_count"] == 2
        assert summary["s"]["is_dictionary"] is False  # 2/10 = 0.2 > 0.1

    def test_explicit_threshold(self):
        summary = stats.compute([{"s": "a"}, {"s": "b"}], dict_threshold=1.0)
        assert summary["s"]["is_dictionary"] is True

    def test_env_var_threshold(self, monkeypatch):
        monkeypatch.setenv("DICT_THRESHOLD", "0.5")
        rows = [{"s": "a"}, {"s": "b"}, {"s": "a"}, {"s": "b"}]
        summary = stats.compute(rows)
        assert summary["s"]["is_dictionary"] is True  # 2/4 = 0.5 <= 0.5

    def test_env_var_invalid_falls_back(self, monkeypatch):
        monkeypatch.setenv("DICT_THRESHOLD", "bogus")
        rows = [{"s": "a"}, {"s": "b"}, {"s": "a"}, {"s": "b"}]
        summary = stats.compute(rows)
        assert summary["s"]["is_dictionary"] is False  # default 0.1

    def test_explicit_threshold_overrides_env(self, monkeypatch):
        monkeypatch.setenv("DICT_THRESHOLD", "1.0")
        summary = stats.compute([{"s": "a"}, {"s": "b"}], dict_threshold=0.1)
        assert summary["s"]["is_dictionary"] is False


class TestFlattenNested:
    def test_dotted_paths_projected(self):
        rows = [
            {"capital_city": {"name": "Paris", "lat": 48.8}},
            {"capital_city": {"name": "Tokyo", "lat": 35.6}},
            {"capital_city": None},
        ]
        summary = stats.compute(rows, flatten_nested=True)
        assert summary["capital_city"]["count"] == 2
        assert summary["capital_city.name"]["count"] == 2
        assert summary["capital_city.name"]["null_count"] == 1
        assert summary["capital_city.lat"]["min"] == 35.6
        assert summary["capital_city.lat"]["max"] == 48.8

    def test_array_of_dicts_exploded(self):
        rows = [
            {"languages": [{"code": "rus"}, {"code": "tgk"}]},
            {"languages": [{"code": "eng"}]},
            {"languages": []},
        ]
        summary = stats.compute(rows, flatten_nested=True)
        assert summary["languages.code"]["count"] == 3
        assert summary["languages.code"]["unique_count"] == 3
        assert summary["languages.code"]["null_count"] == 1  # empty list row

    def test_missing_rows_counted_as_null(self):
        """Rows that never visit a key add to that field's null_count."""
        summary = stats.compute([{"a": {"b": 1}}, {"c": 2}], flatten_nested=True)
        assert summary["a.b"]["null_count"] == 1
        assert summary["c"]["null_count"] == 1

    def test_top_level_scalar_list_not_exploded(self):
        """Explosion only applies to dotted paths; a plain list stays one value."""
        rows = [{"tags": ["x", "y"]}, {"tags": ["z"]}, {"tags": []}]
        summary = stats.compute(rows, flatten_nested=True)
        assert summary["tags"]["count"] == 3
        assert summary["tags"]["unique_count"] == 3

    def test_exploded_list_with_missing_keys(self):
        rows = [{"langs": [{"code": "x"}, {}]}, {"langs": []}]
        summary = stats.compute(rows, flatten_nested=True)
        assert summary["langs.code"]["count"] == 1
        assert summary["langs.code"]["null_count"] == 1

    def test_keep_parents_false(self):
        summary = stats.compute([{"a": {"b": 1}}], flatten_nested=True, keep_nested_parents=False)
        assert "a" not in summary
        assert summary["a.b"]["count"] == 1

    def test_without_flatten_nested_not_projected(self):
        summary = stats.compute([{"capital_city": {"name": "Paris", "lat": 48.8}}])
        assert "capital_city" in summary
        assert "capital_city.name" not in summary
