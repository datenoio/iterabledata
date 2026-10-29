"""JSON backend: msgspec/orjson when installed, the standard library otherwise, same results."""

import datetime
import decimal
import enum
import json
import math
import sys
import types
import uuid

import pytest

from iterable.datatypes.json import JSONIterable
from iterable.datatypes.jsonl import JSONLinesIterable
from iterable.exceptions import FormatParseError, WriteError
from iterable.helpers import jsonbackend


def _fast_installed():
    return jsonbackend._importable("msgspec") and jsonbackend._importable("orjson", jsonbackend.MIN_ORJSON_VERSION)


FAST = pytest.mark.skipif(not _fast_installed(), reason="iterabledata[fast] (orjson, msgspec) is not installed")
BACKENDS = ["stdlib", pytest.param("auto", marks=FAST)]


class Color(enum.Enum):
    RED = "red"


class Size(enum.IntEnum):
    SMALL = 1


RECORDS = [
    {"s": 'a"b\\c\n\r\t\b\f\x00\x1f\x7f é😀', "empty": ""},
    {"ints": [0, -1, 2**63 - 1, -(2**63), 2**64 - 1], "big": 2**70},
    {"floats": [0.1, 1.0, -0.0, 1e16, 1e22, 1.5e300, 123456789.123, 0.0001, 5e-324]},
    {"flags": [True, False, None], "tuple": (1, "x"), "nested": {"a": {"b": [1, {"c": None}]}}},
    {
        "date": datetime.date(2026, 10, 29),
        "dt": datetime.datetime(2026, 10, 29, 8, 30, 1, 120),
        "aware": datetime.datetime(2026, 10, 29, 8, 30, tzinfo=datetime.timezone.utc),
        "time": datetime.time(12, 30),
        "dec": decimal.Decimal("1.50"),
        "uuid": uuid.UUID(int=1),
        "bytes": b"\x01\x02",
        "delta": datetime.timedelta(seconds=5),
        "set": {2, 1},
        "enum": Color.RED,
        "intenum": Size.SMALL,
    },
    {1: "integer key", "x": 1},
]


@pytest.fixture
def backend(request):
    yield jsonbackend.configure(request.param)
    jsonbackend.configure()


def _write_jsonl(path, records):
    with JSONLinesIterable(str(path), mode="w") as dest:
        dest.write_bulk(records)
    return path.read_bytes()


def _read_jsonl(path, **options):
    with JSONLinesIterable(str(path), options=options) as source:
        return list(source)


def test_configure_selects_and_validates(monkeypatch):
    assert jsonbackend.configure("stdlib") == {"decode": "json", "encode": "json"}
    monkeypatch.setenv(jsonbackend.BACKEND_ENV, "stdlib")
    assert jsonbackend.configure() == {"decode": "json", "encode": "json"}
    with pytest.raises(ValueError, match="ITERABLEDATA_JSON_BACKEND"):
        jsonbackend.configure("simdjson")
    monkeypatch.delenv(jsonbackend.BACKEND_ENV)
    jsonbackend.configure()


def test_old_orjson_is_not_used_for_encoding(monkeypatch):
    monkeypatch.setitem(sys.modules, "orjson", types.SimpleNamespace(__version__="3.11.5"))
    try:
        assert jsonbackend.configure("auto")["encode"] == "json"
    finally:
        monkeypatch.undo()
        jsonbackend.configure()


@FAST
def test_jsonl_bytes_identical_across_backends(tmp_path):
    jsonbackend.configure("stdlib")
    try:
        stdlib_bytes = _write_jsonl(tmp_path / "stdlib.jsonl", RECORDS)
        jsonbackend.configure("auto")
        assert jsonbackend.backends() == {"decode": "msgspec", "encode": "orjson"}
        fast_bytes = _write_jsonl(tmp_path / "fast.jsonl", RECORDS)
    finally:
        jsonbackend.configure()
    assert fast_bytes == stdlib_bytes
    # Single-record writes use the same encoder.
    with JSONLinesIterable(str(tmp_path / "single.jsonl"), mode="w") as dest:
        for record in RECORDS:
            dest.write(record)
    assert (tmp_path / "single.jsonl").read_bytes() == stdlib_bytes


@pytest.mark.parametrize("backend", BACKENDS, indirect=True)
def test_output_is_compact_and_values_round_trip(tmp_path, backend):
    path = tmp_path / "out.jsonl"
    # ``split("\n")``: RECORDS[0] contains U+2028, which ``splitlines()`` would split on.
    written = _write_jsonl(path, RECORDS).decode("utf-8").split("\n")

    assert written[3] == '{"flags":[true,false,null],"tuple":[1,"x"],"nested":{"a":{"b":[1,{"c":null}]}}}'
    rows = _read_jsonl(path)
    assert rows[1] == {"ints": [0, -1, 2**63 - 1, -(2**63), 2**64 - 1], "big": 2**70}
    assert rows[2]["floats"] == RECORDS[2]["floats"]
    assert rows[4] == {
        "date": "2026-10-29",
        "dt": "2026-10-29T08:30:01.000120",
        "aware": "2026-10-29T08:30:00+00:00",
        "time": "12:30:00",
        "dec": 1.5,
        "uuid": "00000000-0000-0000-0000-000000000001",
        "bytes": "AQI=",
        "delta": "PT5S",
        "set": [1, 2],
        "enum": "red",
        "intenum": 1,
    }
    assert rows[5] == {"1": "integer key", "x": 1}


@pytest.mark.parametrize("backend", BACKENDS, indirect=True)
def test_small_floats_keep_their_value(tmp_path, backend):
    path = tmp_path / "small.jsonl"
    values = [1e-05, 2.5e-07, -3e-10]
    _write_jsonl(path, [{"v": values}])
    assert _read_jsonl(path) == [{"v": values}]


@pytest.mark.parametrize("backend", BACKENDS, indirect=True)
def test_non_finite_floats_are_written_as_null(tmp_path, backend):
    path = tmp_path / "nan.jsonl"
    written = _write_jsonl(path, [{"nan": math.nan, "inf": [math.inf, -math.inf], "ok": 1.5}])
    assert written == b'{"nan":null,"inf":[null,null],"ok":1.5}\n'


@pytest.mark.parametrize("backend", BACKENDS, indirect=True)
def test_reader_accepts_what_json_accepts(tmp_path, backend):
    path = tmp_path / "in.jsonl"
    path.write_text('{"a": NaN}\n{"b": 18446744073709551616}\n{"c": "\\ud83d\\ude00"}\n', encoding="utf-8")
    rows = _read_jsonl(path)
    assert math.isnan(rows[0]["a"])
    assert rows[1] == {"b": 18446744073709551616}
    assert type(rows[1]["b"]) is int
    assert rows[2] == {"c": "😀"}


@pytest.mark.parametrize("backend", BACKENDS, indirect=True)
def test_read_bulk_matches_row_iteration(tmp_path, backend):
    path = tmp_path / "rows.jsonl"
    lines = [json.dumps({"id": i}) if i % 4 else "" for i in range(1, 30)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    expected = [{"id": i} for i in range(1, 30) if i % 4]

    with JSONLinesIterable(str(path)) as source:
        chunks = []
        while chunk := source.read_bulk(5):
            chunks.append(chunk)
        assert source.pos == len(expected)
    assert all(len(chunk) == 5 for chunk in chunks[:-1])
    assert [row for chunk in chunks for row in chunk] == expected == _read_jsonl(path)


@pytest.mark.parametrize("backend", BACKENDS, indirect=True)
@pytest.mark.parametrize("bulk", [False, True])
def test_parse_errors_report_line_numbers(tmp_path, backend, bulk):
    path = tmp_path / "bad.jsonl"
    path.write_text('{"id": 1}\n\n{"id": 2}\n{"id": \n{"id": 3}\n', encoding="utf-8")

    with JSONLinesIterable(str(path)) as source, pytest.raises(FormatParseError) as excinfo:
        if bulk:
            source.read_bulk(10)
        else:
            list(source)
    assert excinfo.value.row_number == 4
    assert excinfo.value.original_line == '{"id": '

    rows = _read_jsonl(path, on_error="skip")
    assert rows == [{"id": 1}, {"id": 2}, {"id": 3}]
    with JSONLinesIterable(str(path), options={"on_error": "skip"}) as source:
        assert source.read_bulk(10) == rows


@pytest.mark.parametrize("backend", BACKENDS, indirect=True)
def test_unknown_types_raise_when_requested(tmp_path, backend):
    with JSONLinesIterable(str(tmp_path / "x.jsonl"), mode="w", options={"on_unknown_type": "raise"}) as dest:
        with pytest.raises(WriteError, match="Cannot serialize value of type"):
            dest.write_bulk([{"obj": object()}])


@pytest.mark.parametrize("backend", BACKENDS, indirect=True)
def test_json_array_round_trip(tmp_path, backend):
    path = tmp_path / "rows.json"
    with JSONIterable(str(path), mode="w") as dest:
        dest.write_bulk(RECORDS[:4])
        dest.write({"last": True})
    text = path.read_text(encoding="utf-8")
    assert text.startswith('[{"s":') and text.endswith(',{"last":true}]')
    with JSONIterable(str(path)) as source:
        rows = list(source)
    assert rows[1:] == [json.loads(json.dumps(r)) for r in RECORDS[1:4]] + [{"last": True}]
    assert rows[0] == RECORDS[0]
