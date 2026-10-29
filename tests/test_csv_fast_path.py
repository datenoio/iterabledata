"""The CSV fast path (``csv.reader``/``csv.writer``) keeps ``DictReader``/``DictWriter`` semantics."""

import csv
import io

import pytest

from iterable.datatypes.csv import CSVIterable
from iterable.exceptions import FormatParseError

DIALECTS = {
    "default": {},
    "semicolon": {"delimiter": ";", "quotechar": "'"},
    "escape": {"escapechar": "\\", "doublequote": False},
}

INPUTS = {
    "plain": "id,name,value\n1,a,10\n2,b,20\n",
    "short_rows": "id,name,value\n1,a\n2\n3,c,30\n",
    "long_rows": "id,name\n1,a,extra\n2,b,x,y\n3,c\n",
    "blank_lines": "id,name\n\n1,a\n\n\n2,b\n\n",
    "quoted_newlines": 'id,text\n1,"line one\nline two"\n2,"say ""hi"", ok"\n',
    "crlf": "id,name\r\n1,a\r\n2,b\r\n",
    "no_trailing_newline": "id,name\n1,a\n2,b",
    "header_only": "id,name\n",
    "empty": "",
    "bom": "﻿id,name\n1,a\n",
}


def _dictreader(text, keys=None, **dialect):
    return list(csv.DictReader(io.StringIO(text, newline=""), fieldnames=keys, **dialect))


def _write_text(tmp_path, name, text):
    path = tmp_path / name
    path.write_bytes(text.encode("utf-8"))
    return path


def _open(path, **options):
    return CSVIterable(str(path), encoding="utf-8", options=dict(options))


@pytest.mark.parametrize("name", list(INPUTS))
def test_rows_match_dictreader(tmp_path, name):
    text = INPUTS[name]
    path = _write_text(tmp_path, "in.csv", text)
    expected = _dictreader(text)

    with _open(path) as source:
        assert list(source) == expected
    with _open(path) as source:
        chunks = []
        while chunk := source.read_bulk(2):
            chunks.append(chunk)
        assert [row for chunk in chunks for row in chunk] == expected
        assert all(len(chunk) == 2 for chunk in chunks[:-1])
        assert source.pos == len(expected)


@pytest.mark.parametrize("dialect", list(DIALECTS))
def test_dialects_match_dictreader(tmp_path, dialect):
    options = DIALECTS[dialect]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=["id", "text"], **options)
    writer.writeheader()
    writer.writerows([{"id": 1, "text": 'a;b,"c"'}, {"id": 2, "text": "it's\nhere"}])
    text = buffer.getvalue()
    path = _write_text(tmp_path, "in.csv", text)

    with _open(path, **options) as source:
        assert list(source) == _dictreader(text, **options)


def test_explicit_keys_match_dictreader(tmp_path):
    text = "1,a\n2,b,c\n3\n"
    path = _write_text(tmp_path, "in.csv", text)
    with _open(path, keys=["id", "name"]) as source:
        assert source.read_bulk(10) == _dictreader(text, keys=["id", "name"])


def test_reader_exposes_dictreader_attributes(tmp_path):
    path = _write_text(tmp_path, "in.csv", "id,name\n1,a\n2,b\n")
    with _open(path) as source:
        assert source.reader.fieldnames == ["id", "name"]
        next(source)
        assert source.reader.line_num == 2


RECORDS = [
    {"id": 1, "name": "a", "note": 'quote " and, comma'},
    {"id": 2, "name": None, "note": "multi\nline"},
    {"note": "reordered", "id": 3, "name": "c"},
    {"id": 4},
]


@pytest.mark.parametrize("dialect", list(DIALECTS))
@pytest.mark.parametrize("bulk", [False, True])
def test_writer_matches_dictwriter(tmp_path, dialect, bulk):
    options = DIALECTS[dialect]
    expected = io.StringIO(newline="")
    writer = csv.DictWriter(expected, fieldnames=["id", "name", "note"], **options)
    writer.writeheader()
    writer.writerows(RECORDS)

    path = tmp_path / "out.csv"
    with CSVIterable(str(path), mode="w", options=dict(options)) as dest:
        if bulk:
            dest.write_bulk(RECORDS)
        else:
            for record in RECORDS:
                dest.write(record)
    assert path.read_bytes().decode("utf-8") == expected.getvalue()


@pytest.mark.parametrize("keys", [["only"], ["a", "b"]])
def test_writer_rejects_unknown_fields_like_dictwriter(tmp_path, keys):
    record = {**dict.fromkeys(keys, 1), "extra": 2}
    with pytest.raises(ValueError) as expected:
        csv.DictWriter(io.StringIO(), fieldnames=keys).writerow(record)
    with CSVIterable(str(tmp_path / "out.csv"), mode="w", keys=keys) as dest:
        with pytest.raises(ValueError) as actual:
            dest.write_bulk([dict.fromkeys(keys, 1), record])
    assert str(actual.value) == str(expected.value)


def test_single_column_writer(tmp_path):
    records = [{"id": 1}, {"id": None}, {"id": "x,y"}]
    expected = io.StringIO(newline="")
    writer = csv.DictWriter(expected, fieldnames=["id"])
    writer.writeheader()
    writer.writerows(records)

    path = tmp_path / "one.csv"
    with CSVIterable(str(path), mode="w") as dest:
        dest.write_bulk(records)
    assert path.read_bytes().decode("utf-8") == expected.getvalue() == 'id\r\n1\r\n""\r\n"x,y"\r\n'


@pytest.fixture
def small_field_limit():
    previous = csv.field_size_limit(8)
    yield
    csv.field_size_limit(previous)


@pytest.mark.parametrize("bulk", [False, True])
def test_parse_errors_name_the_line(tmp_path, small_field_limit, bulk):
    path = _write_text(tmp_path, "bad.csv", "id,name\n1,a\n2,abcdefghijkl\n3,c\n")
    with _open(path) as source, pytest.raises(FormatParseError) as excinfo:
        if bulk:
            source.read_bulk(10)
        else:
            list(source)
    assert excinfo.value.row_number == 3
    assert "field larger than field limit" in str(excinfo.value)

    with _open(path, on_error="skip") as source:
        rows = source.read_bulk(10) if bulk else list(source)
    assert rows == [{"id": "1", "name": "a"}, {"id": "3", "name": "c"}]
