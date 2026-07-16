"""Tests for the opt-in native columnar conversion path."""

import json

import pytest

from iterable.convert import BatchSelection, convert

pyarrow = pytest.importorskip("pyarrow")


def test_native_parquet_batch_conversion_with_projection(tmp_path):
    source = tmp_path / "source.parquet"
    target = tmp_path / "target.parquet"
    table = pyarrow.table({"id": [1, 2, 3], "name": ["a", "b", "c"]})
    pyarrow.parquet.write_table(table, source)

    result = convert(
        str(source),
        str(target),
        use_native_batch=True,
        selection=BatchSelection(columns=("id",), batch_size=2),
    )

    assert result.rows_in == result.rows_out == 3
    assert pyarrow.parquet.read_table(target).column_names == ["id"]


def test_native_batch_request_falls_back_for_jsonl(tmp_path):
    source = tmp_path / "source.jsonl"
    target = tmp_path / "target.jsonl"
    source.write_text(json.dumps({"id": 1}) + "\n", encoding="utf-8")

    result = convert(str(source), str(target), use_native_batch=True)

    assert result.rows_in == result.rows_out == 1
    assert json.loads(target.read_text(encoding="utf-8")) == {"id": 1}


def test_native_batch_strict_mode_rejects_row_only_endpoint(tmp_path):
    source = tmp_path / "source.jsonl"
    target = tmp_path / "target.jsonl"
    source.write_text(json.dumps({"id": 1}) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Native batch conversion"):
        convert(str(source), str(target), use_native_batch=True, strict_native=True)
