"""Parquet writer: one Arrow conversion per batch, unchanged errors, row groups and values."""

import pytest

pyarrow = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")

from iterable.datatypes import parquet as parquet_module  # noqa: E402
from iterable.datatypes.parquet import ParquetIterable  # noqa: E402
from iterable.exceptions import WriteError  # noqa: E402


def _rows(start, count):
    return [{"id": i, "name": f"n{i}", "score": i * 0.5} for i in range(start, start + count)]


def _read(path):
    return pq.read_table(path).to_pylist()


class _CountingPyArrow:
    """``pyarrow`` stand-in that records the size of every ``Table.from_pylist`` call."""

    def __init__(self):
        self.calls = []
        calls = self.calls

        class Table:
            def __getattr__(self, name):
                return getattr(pyarrow.Table, name)

            @staticmethod
            def from_pylist(records, *args, **kwargs):
                calls.append(len(records))
                return pyarrow.Table.from_pylist(records, *args, **kwargs)

        self.Table = Table()

    def __getattr__(self, name):
        return getattr(pyarrow, name)


def test_each_batch_is_converted_once(tmp_path, monkeypatch):
    counting = _CountingPyArrow()
    monkeypatch.setattr(parquet_module, "pyarrow", counting)
    calls = counting.calls
    path = tmp_path / "out.parquet"
    with ParquetIterable(str(path), mode="w", batch_size=4) as dest:
        for start in range(0, 20, 2):
            dest.write_bulk(_rows(start, 2))
    monkeypatch.undo()

    # The first flush infers the schema from the buffered 4 rows; every later batch once.
    assert calls == [4] + [2] * 8
    assert _read(path) == _rows(0, 20)


def test_row_group_layout(tmp_path):
    path = tmp_path / "groups.parquet"
    with ParquetIterable(str(path), mode="w", row_group_size=3) as dest:
        for start in range(0, 10, 2):
            dest.write_bulk(_rows(start, 2))
    metadata = pq.ParquetFile(path).metadata
    assert [metadata.row_group(i).num_rows for i in range(metadata.num_row_groups)] == [4, 4, 2]
    assert _read(path) == _rows(0, 10)


def test_schema_mismatch_raises_at_the_offending_batch(tmp_path):
    path = tmp_path / "bad.parquet"
    dest = ParquetIterable(str(path), mode="w", batch_size=2)
    try:
        dest.write_bulk(_rows(0, 2))
        dest.write_bulk(_rows(2, 2))
        with pytest.raises(WriteError) as excinfo:
            dest.write_bulk([{"id": "not a number", "name": "x", "score": 1.0}])
        assert excinfo.value.error_code == "SCHEMA_ALIGNMENT_FAILED"
        dest.write_bulk(_rows(4, 2))
    finally:
        dest.close()
    assert _read(path) == _rows(0, 6)


def test_missing_and_unknown_keys_follow_the_schema(tmp_path):
    path = tmp_path / "keys.parquet"
    with ParquetIterable(str(path), mode="w", batch_size=1) as dest:
        dest.write_bulk([{"id": 1, "name": "a"}])
        dest.write_bulk([{"name": "b", "extra": True}, {"id": 3}])
    assert _read(path) == [{"id": 1, "name": "a"}, {"id": None, "name": "b"}, {"id": 3, "name": None}]


def test_extended_json_is_unwrapped_in_any_batch(tmp_path):
    path = tmp_path / "ext.parquet"
    with ParquetIterable(str(path), mode="w", batch_size=1) as dest:
        dest.write_bulk([{"id": {"$numberLong": "1"}, "tags": ["a"]}])
        dest.write_bulk([{"id": 2, "tags": ["b"]}])
        dest.write_bulk([{"id": {"$numberLong": "3"}, "tags": []}])
    assert _read(path) == [{"id": 1, "tags": ["a"]}, {"id": 2, "tags": ["b"]}, {"id": 3, "tags": []}]
