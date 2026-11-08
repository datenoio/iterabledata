import pytest
from fixdata import FIXTURES

from iterable.datatypes import JSONIterable


def test_json_has_tables():
    """Test JSON doesn't support tables"""
    assert JSONIterable.has_tables() is False


def test_json_list_tables():
    """Test JSON list_tables returns None"""
    iterable = JSONIterable("fixtures/2cols6rows_array.json")
    assert iterable.list_tables() is None
    assert iterable.list_tables("fixtures/2cols6rows_array.json") is None
    iterable.close()


class TestJSON:
    def test_id(self):
        datatype_id = JSONIterable.id()
        assert datatype_id == "json"

    def test_flatonly(self):
        flag = JSONIterable.is_flatonly()
        assert not flag

    def test_openclose(self):
        iterable = JSONIterable("fixtures/2cols6rows_array.json")
        iterable.close()

    def test_read_bulk_returns_n_records(self):
        iterable = JSONIterable("fixtures/2cols6rows_array.json")
        chunk = iterable.read_bulk(3)
        assert len(chunk) == 3
        from fixdata import FIXTURES

        assert chunk == FIXTURES[:3]
        iterable.close()

    def test_stop_iteration_after_exhaustion(self):
        iterable = JSONIterable("fixtures/2cols6rows_array.json")
        for _ in range(6):
            _ = iterable.read()
        with pytest.raises(StopIteration):
            _ = iterable.read()
        iterable.close()

    def test_parsesimple_readone(self):
        iterable = JSONIterable("fixtures/2cols6rows_array.json")
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.close()

    def test_parsesimple_reset(self):
        iterable = JSONIterable("fixtures/2cols6rows_tag.json", tagname="persons")
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = iterable.read()
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_next(self):
        iterable = JSONIterable("fixtures/2cols6rows_array.json")
        row = next(iterable)
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = next(iterable)
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_count(self):
        iterable = JSONIterable("fixtures/2cols6rows_array.json")
        n = 0
        for _row in iterable:
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_parsesimple_iterateall(self):
        iterable = JSONIterable("fixtures/2cols6rows_array.json")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()


@pytest.mark.parametrize(
    ("document", "key", "records"),
    [
        ({"odata.metadata": "x", "value": [{"a": 1}, {"a": 2}]}, "value", [{"a": 1}, {"a": 2}]),
        ({"@context": {}, "@graph": [{"@id": "1"}]}, "@graph", [{"@id": "1"}]),
        ({"meta": [{"m": 1}], "rows": [{"b": 1}, {"b": 2}]}, "rows", [{"b": 1}, {"b": 2}]),
        ({"columns": ["a"], "data": [[1], [2]]}, None, [{"columns": ["a"], "data": [[1], [2]]}]),
        ({"name": "x", "value": 1}, None, [{"name": "x", "value": 1}]),
    ],
)
def test_json_object_root_without_tagname(tmp_path, document, key, records):
    import json

    from iterable.helpers.detect import open_iterable

    path = tmp_path / "root.json"
    path.write_text(json.dumps(document))
    with open_iterable(str(path)) as source:
        assert list(source) == records
        assert source.tagname == key


def test_json_object_root_in_streaming_mode(tmp_path):
    pytest.importorskip("ijson")
    import json

    from iterable.helpers.detect import open_iterable

    path = tmp_path / "big.json"
    path.write_text(json.dumps({"meta": {"n": 1}, "value": [{"i": i, "s": "x" * 200} for i in range(60000)]}))
    with open_iterable(str(path)) as source:
        assert source.is_streaming()
        assert source.tagname == "value"
        assert next(source)["i"] == 0
        assert sum(1 for _ in source) == 59999
    single = tmp_path / "big_object.json"
    single.write_text(json.dumps({"name": "x" * 11_000_000}))
    with open_iterable(str(single)) as source:
        rows = list(source)
        assert source.is_streaming()
        assert len(rows) == 1 and len(rows[0]["name"]) == 11_000_000
