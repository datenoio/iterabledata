"""Native CSV batches: Arrow record batches into Parquet/Arrow writers, same values as the row path."""

import gzip

import pytest

pyarrow = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")

from iterable.convert import convert  # noqa: E402
from iterable.datatypes.csv import CSVIterable  # noqa: E402
from iterable.exceptions import FormatParseError  # noqa: E402

CSV_TEXT = 'id,code,amount,note,empty\n1,007,1.50,"comma, and ""quote""",\n2,,-3,"multi\nline",\n\n3,0x1F,1e5,plain,\n'


@pytest.fixture
def csv_file(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text(CSV_TEXT, encoding="utf-8")
    return path


def _parquet_rows(path):
    return pq.read_table(path).to_pylist()


def _convert_both(src, tmp_path, suffix="parquet", **kwargs):
    row_out = tmp_path / f"row.{suffix}"
    native_out = tmp_path / f"native.{suffix}"
    row_result = convert(str(src), str(row_out), **kwargs)
    native_result = convert(str(src), str(native_out), use_native_batch=True, strict_native=True, **kwargs)
    return row_result, native_result, row_out, native_out


def test_native_parquet_matches_row_path(csv_file, tmp_path):
    row_result, native_result, row_out, native_out = _convert_both(csv_file, tmp_path)

    assert native_result.rows_in == native_result.rows_out == row_result.rows_out == 3
    assert _parquet_rows(native_out) == _parquet_rows(row_out)
    assert _parquet_rows(native_out)[1] == {"id": "2", "code": "", "amount": "-3", "note": "multi\nline", "empty": ""}
    schema = pq.read_schema(native_out)
    assert all(field.type == pyarrow.string() for field in schema)


def test_native_path_does_not_build_rows(csv_file, tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("row path used")

    monkeypatch.setattr(CSVIterable, "read_bulk", fail)
    monkeypatch.setattr(CSVIterable, "read_batches", fail)
    result = convert(str(csv_file), str(tmp_path / "out.parquet"), use_native_batch=True, strict_native=True)
    assert result.rows_out == 3


def test_native_arrow_ipc_matches_row_path(csv_file, tmp_path):
    _, native_result, row_out, native_out = _convert_both(csv_file, tmp_path, suffix="arrow")
    assert native_result.rows_out == 3
    read = lambda path: pyarrow.ipc.open_file(str(path)).read_all().to_pylist()  # noqa: E731
    assert read(native_out) == read(row_out)


def test_native_gzip_source(tmp_path):
    src = tmp_path / "data.csv.gz"
    with gzip.open(src, "wt", encoding="utf-8", newline="") as f:
        f.write(CSV_TEXT)
    _, native_result, row_out, native_out = _convert_both(src, tmp_path)
    assert native_result.rows_out == 3
    assert _parquet_rows(native_out) == _parquet_rows(row_out)


def test_native_dialect_and_projection(tmp_path):
    src = tmp_path / "data.tsv"
    src.write_text("id\tname\tvalue\n1\ta;b\t10\n2\t'x\ty'\t20\n", encoding="utf-8")
    selection = {"columns": ["value", "id"]}
    kwargs = {"iterableargs": {"quotechar": "'"}, "selection": selection}
    _, native_result, row_out, native_out = _convert_both(src, tmp_path, **kwargs)
    assert native_result.rows_out == 2
    assert _parquet_rows(native_out) == [{"value": "10", "id": "1"}, {"value": "20", "id": "2"}]
    assert _parquet_rows(native_out) == _parquet_rows(row_out)


def test_unsupported_selection_falls_back_to_rows(csv_file, tmp_path):
    out = tmp_path / "out.parquet"
    result = convert(str(csv_file), str(out), use_native_batch=True, selection={"row_range": [1, 3]})
    assert result.rows_out == 2
    assert [row["id"] for row in _parquet_rows(out)] == ["2", "3"]
    with pytest.raises(NotImplementedError):
        convert(str(csv_file), str(out), selection={"row_range": [1, 3]}, use_native_batch=True, strict_native=True)


def test_ragged_rows_raise_on_the_native_path(tmp_path):
    src = tmp_path / "ragged.csv"
    src.write_text("id,name\n1,a\n2\n", encoding="utf-8")
    with pytest.raises(FormatParseError, match="use_native_batch=False"):
        convert(str(src), str(tmp_path / "out.parquet"), use_native_batch=True)
    # The row path pads short rows, as DictReader does.
    convert(str(src), str(tmp_path / "rows.parquet"))
    assert _parquet_rows(tmp_path / "rows.parquet") == [{"id": "1", "name": "a"}, {"id": "2", "name": None}]


def test_read_batches_rows_for_non_arrow_writers(csv_file):
    with CSVIterable(str(csv_file)) as source:
        batches = list(source.read_batches())
    assert [row["id"] for batch in batches for row in batch] == ["1", "2", "3"]
