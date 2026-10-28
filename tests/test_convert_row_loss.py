"""convert() must not drop rows silently: flat-output flattening and write error policies."""

import csv
import json

import pytest

from iterable.convert import bulk_convert, convert
from iterable.datatypes.jsonl import JSONLinesIterable
from iterable.exceptions import WriteError


def _write_jsonl(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def _read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_nested_jsonl_to_csv_writes_every_row(tmp_path):
    src = tmp_path / "n.jsonl"
    _write_jsonl(src, [{"id": i, "meta": {"a": i, "tags": ["x", "y"]}} for i in range(3)])
    out = tmp_path / "n.csv"

    result = convert(str(src), str(out))

    rows = _read_csv(out)
    assert result.rows_in == result.rows_out == 3
    assert list(rows[0]) == ["id", "meta.a", "meta.tags"]
    assert rows[2] == {"id": "2", "meta.a": "2", "meta.tags": '["x", "y"]'}


def test_is_flatten_keeps_legacy_string_form(tmp_path):
    src = tmp_path / "n.jsonl"
    _write_jsonl(src, [{"id": 1, "meta": {"a": 1}}])
    out = tmp_path / "n.csv"
    convert(str(src), str(out), is_flatten=True)
    assert _read_csv(out) == [{"id": "1", "meta": "{'a': 1}"}]


@pytest.fixture
def late_field_source(tmp_path):
    src = tmp_path / "late.jsonl"
    _write_jsonl(src, [{"id": 1}, {"id": 2}, {"id": 3, "late": "x"}])
    return src


def test_field_after_scan_limit_raises(late_field_source, tmp_path):
    with pytest.raises(WriteError, match="late"):
        convert(str(late_field_source), str(tmp_path / "o.csv"), scan_limit=2)


def test_field_after_scan_limit_ignored_on_request(late_field_source, tmp_path):
    out = tmp_path / "o.csv"
    result = convert(str(late_field_source), str(out), scan_limit=2, extra_fields="ignore")
    assert result.rows_out == 3
    assert _read_csv(out) == [{"id": "1"}, {"id": "2"}, {"id": "3"}]


@pytest.fixture
def failing_second_batch(monkeypatch):
    original = JSONLinesIterable.write_bulk
    calls = {"n": 0}

    def write_bulk(self, records):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("disk full")
        return original(self, records)

    monkeypatch.setattr(JSONLinesIterable, "write_bulk", write_bulk)


def test_batch_write_failure_raises(tmp_path, failing_second_batch):
    src = tmp_path / "in.jsonl"
    _write_jsonl(src, [{"id": i} for i in range(5)])
    with pytest.raises(WriteError, match="rows 3-4") as excinfo:
        convert(str(src), str(tmp_path / "out.jsonl"), batch_size=2)
    assert isinstance(excinfo.value.__cause__, OSError)


def test_batch_write_failure_skip_accounting(tmp_path, failing_second_batch):
    src = tmp_path / "in.jsonl"
    _write_jsonl(src, [{"id": i} for i in range(5)])
    result = convert(str(src), str(tmp_path / "out.jsonl"), batch_size=2, on_write_error="skip")
    assert result.rows_in == 5
    assert result.rows_skipped == 2
    assert result.rows_out + result.rows_skipped == result.rows_in
    assert any(isinstance(e, WriteError) for e in result.errors)


def test_bulk_convert_reports_failed_file(tmp_path, failing_second_batch):
    src_dir = tmp_path / "in"
    src_dir.mkdir()
    _write_jsonl(src_dir / "a.jsonl", [{"id": i} for i in range(5)])
    out_dir = tmp_path / "out"
    result = bulk_convert(str(src_dir / "*.jsonl"), str(out_dir), to_ext="jsonl", batch_size=2)
    assert result.failed_files == 1
    assert isinstance(result.file_results[0].error, WriteError)


@pytest.mark.parametrize(("name", "value"), [("extra_fields", "drop"), ("on_write_error", "ignore")])
def test_invalid_policy_values(tmp_path, name, value):
    src = tmp_path / "in.jsonl"
    _write_jsonl(src, [{"id": 1}])
    with pytest.raises(ValueError, match=name):
        convert(str(src), str(tmp_path / "out.csv"), **{name: value})
