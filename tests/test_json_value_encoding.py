"""Type fidelity of JSON-family writers and size-independent JSON decoding."""

import datetime
import decimal
import enum
import json
import struct
import uuid

import pytest

from iterable import open_iterable
from iterable.convert import convert
from iterable.datatypes.json import JSONIterable
from iterable.exceptions import WriteError
from iterable.helpers.detect import DATATYPE_REGISTRY, _load_symbol
from iterable.helpers.jsonvalues import encode_default, iso_duration, make_json_default

UTC = datetime.timezone.utc

RECORD = {
    "time": datetime.time(12, 30),
    "date": datetime.date(2026, 10, 28),
    "naive": datetime.datetime(2026, 10, 28, 9, 15, 0),
    "aware": datetime.datetime(2026, 10, 28, 9, 15, 0, tzinfo=UTC),
    "dec": decimal.Decimal("1.50"),
    "uuid": uuid.UUID(int=1),
    "bytes": b"\x01\x02",
    "delta": datetime.timedelta(seconds=5),
    "set": {2, 1},
    "none": None,
}

EXPECTED = {
    "time": "12:30:00",
    "date": "2026-10-28",
    "naive": "2026-10-28T09:15:00",
    "aware": "2026-10-28T09:15:00+00:00",
    "dec": 1.5,
    "uuid": "00000000-0000-0000-0000-000000000001",
    "bytes": "AQI=",
    "delta": "PT5S",
    "set": [1, 2],
    "none": None,
}


def _written_objects(path, fmt):
    text = path.read_text(encoding="utf-8")
    if fmt == "json":
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


@pytest.mark.parametrize("fmt", ["jsonl", "json", "gelf", "jsonld"])
def test_writers_keep_every_value(tmp_path, fmt):
    path = tmp_path / f"out.{fmt}"
    with open_iterable(str(path), mode="w") as it:
        it.write(dict(RECORD))
    (obj,) = _written_objects(path, fmt)
    for key, value in EXPECTED.items():
        assert obj[key] == value, key


def test_json_and_jsonl_agree(tmp_path):
    with open_iterable(str(tmp_path / "a.json"), mode="w") as it:
        it.write_bulk([dict(RECORD)])
    with open_iterable(str(tmp_path / "a.jsonl"), mode="w") as it:
        it.write_bulk([dict(RECORD)])
    assert _written_objects(tmp_path / "a.json", "json") == _written_objects(tmp_path / "a.jsonl", "jsonl")


class _Color(enum.Enum):
    RED = "red"


PAYLOAD = {**RECORD, "enum": _Color.RED, "text": "naïve 日本"}
PAYLOAD_EXPECTED = {**EXPECTED, "enum": "red", "text": "naïve 日本"}

# Binary containers that store the whole record as one JSON document.
RECORD_PAYLOAD_FORMATS = ("recordio", "tfrecord", "flink")
# Binary containers that JSON-encode the ``value`` of a key/value record.
KEY_VALUE_PAYLOAD_FORMATS = ("kafka", "pulsar", "sequencefile", "beam")

# Smallest header the SequenceFile reader accepts (version, empty key/value class names,
# compression flags, no metadata, sync marker); the writer does not emit one.
SEQUENCEFILE_HEADER = b"\x06" + struct.pack(">II", 0, 0) + b"\x00\x00" + struct.pack(">I", 0) + b"\x00" * 16


def _binary_class(fmt):
    module_path, symbol = DATATYPE_REGISTRY[fmt]
    try:
        return _load_symbol(module_path, symbol)
    except ImportError as exc:
        pytest.skip(f"Optional dependency missing for {fmt!r}: {exc}")


def _binary_round_trip(fmt, path, record, **options):
    cls = _binary_class(fmt)
    with cls(str(path), mode="w", options=options) as dest:
        dest.write(record)
    raw = path.read_bytes()
    if fmt == "sequencefile":
        path.write_bytes(SEQUENCEFILE_HEADER + raw)
    with cls(str(path)) as source:
        return raw, list(source)


@pytest.mark.parametrize("fmt", RECORD_PAYLOAD_FORMATS + KEY_VALUE_PAYLOAD_FORMATS)
def test_binary_json_payloads_keep_every_value(tmp_path, fmt):
    record = dict(PAYLOAD) if fmt in RECORD_PAYLOAD_FORMATS else {"key": "k1", "value": dict(PAYLOAD)}
    raw, (row,) = _binary_round_trip(fmt, tmp_path / f"out.{fmt}", record)
    payload = row if fmt in RECORD_PAYLOAD_FORMATS else row["value"]
    for key, value in PAYLOAD_EXPECTED.items():
        assert payload[key] == value, key
    assert "naïve 日本".encode() in raw


@pytest.mark.parametrize("fmt", RECORD_PAYLOAD_FORMATS + KEY_VALUE_PAYLOAD_FORMATS)
def test_binary_json_payloads_honor_writer_options(tmp_path, fmt):
    value = {"dec": decimal.Decimal("1.50")}
    record = dict(value) if fmt in RECORD_PAYLOAD_FORMATS else {"key": "k1", "value": value}
    _, (row,) = _binary_round_trip(fmt, tmp_path / f"out.{fmt}", record, decimal="string")
    payload = row if fmt in RECORD_PAYLOAD_FORMATS else row["value"]
    assert payload["dec"] == "1.50"


def test_numpy_scalars_and_arrays():
    np = pytest.importorskip("numpy")
    assert json.loads(
        json.dumps({"i": np.int64(3), "f": np.float32(0.5), "a": np.arange(2)}, default=encode_default)
    ) == {
        "i": 3,
        "f": 0.5,
        "a": [0, 1],
    }


@pytest.mark.parametrize(
    ("value", "auto", "string"),
    [
        (decimal.Decimal("1.50"), 1.5, "1.50"),
        (decimal.Decimal("1.23"), 1.23, "1.23"),
        (decimal.Decimal("12345678901234567890.123456789"), "12345678901234567890.123456789", None),
        (decimal.Decimal("NaN"), "NaN", "NaN"),
    ],
)
def test_decimal_modes(value, auto, string):
    assert make_json_default("auto")(value) == auto
    assert make_json_default("string")(value) == (string or str(value))


def test_decimal_string_option_on_writer(tmp_path):
    path = tmp_path / "d.jsonl"
    with open_iterable(str(path), mode="w", iterableargs={"decimal": "string"}) as it:
        it.write({"dec": decimal.Decimal("1.50")})
    assert path.read_text(encoding="utf-8").strip() == '{"dec":"1.50"}'


class _Opaque:
    def __str__(self):
        return "opaque"


def test_unknown_type_written_as_text_by_default(tmp_path):
    path = tmp_path / "u.jsonl"
    with open_iterable(str(path), mode="w") as it:
        it.write({"v": _Opaque()})
    assert json.loads(path.read_text(encoding="utf-8")) == {"v": "opaque"}


def test_unknown_type_raise_option(tmp_path):
    path = tmp_path / "u.jsonl"
    with open_iterable(str(path), mode="w", iterableargs={"on_unknown_type": "raise"}) as it:
        with pytest.raises(WriteError, match="_Opaque"):
            it.write({"v": _Opaque()})
    assert path.read_text(encoding="utf-8") == ""


def test_invalid_modes_rejected():
    with pytest.raises(ValueError, match="decimal"):
        make_json_default("float")
    with pytest.raises(ValueError, match="on_unknown_type"):
        make_json_default(on_unknown_type="null")


@pytest.mark.parametrize(
    ("delta", "expected"),
    [
        (datetime.timedelta(0), "PT0S"),
        (datetime.timedelta(days=1), "P1D"),
        (datetime.timedelta(days=1, hours=2, minutes=3, seconds=4, milliseconds=500), "P1DT2H3M4.5S"),
        (datetime.timedelta(seconds=-5), "-PT5S"),
        (datetime.timedelta(microseconds=1), "PT0.000001S"),
    ],
)
def test_iso_duration(delta, expected):
    assert iso_duration(delta) == expected


@pytest.fixture
def float_array(tmp_path):
    path = tmp_path / "floats.json"
    path.write_text(json.dumps([{"id": i, "amount": i + 0.5} for i in range(5)]), encoding="utf-8")
    return path


def _read_with_streaming(path, monkeypatch, streaming):
    monkeypatch.setattr(JSONIterable, "_should_use_streaming", lambda self: streaming)
    with open_iterable(str(path)) as it:
        return list(it)


def test_json_types_do_not_depend_on_streaming(float_array, monkeypatch):
    pytest.importorskip("ijson")
    in_memory = _read_with_streaming(float_array, monkeypatch, False)
    streamed = _read_with_streaming(float_array, monkeypatch, True)
    assert streamed == in_memory
    assert all(type(row["amount"]) is float for row in streamed)


def test_streamed_json_to_jsonl_keeps_fractions(float_array, tmp_path, monkeypatch):
    pytest.importorskip("ijson")
    monkeypatch.setattr(JSONIterable, "_should_use_streaming", lambda self: True)
    out = tmp_path / "floats.jsonl"
    convert(str(float_array), str(out))
    assert [row["amount"] for row in _written_objects(out, "jsonl")] == [0.5, 1.5, 2.5, 3.5, 4.5]
