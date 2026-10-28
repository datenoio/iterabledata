"""Regression tests: JSON-family writers must keep ``datetime.time`` values.

The JSONL, GELF, and JSON-LD writers used a ``default=`` handler that only knew about
``date``/``datetime`` and silently wrote ``null`` for ``time`` values (e.g. TIME columns
coming from DuckDB or Parquet).
"""

import datetime

import pytest

from iterable.datatypes import GELIterable, JSONIterable, JSONLDIterable, JSONLinesIterable

RECORD = {
    "id": 1,
    "t": datetime.time(10, 30),
    "t_us": datetime.time(10, 30, 0, 123),
    "d": datetime.date(2024, 1, 2),
}

WRITERS = [
    pytest.param(JSONIterable, "json", id="json"),
    pytest.param(JSONLinesIterable, "jsonl", id="jsonl"),
    pytest.param(GELIterable, "gelf", id="gelf"),
    pytest.param(JSONLDIterable, "jsonld", id="jsonld"),
]


def _roundtrip(cls, path, bulk):
    writer = cls(str(path), mode="w")
    if bulk:
        writer.write_bulk([RECORD])
    else:
        writer.write(RECORD)
    writer.close()
    reader = cls(str(path))
    rows = list(reader)
    reader.close()
    return rows


@pytest.mark.parametrize("bulk", [False, True], ids=["write", "write_bulk"])
@pytest.mark.parametrize("cls,ext", WRITERS)
def test_time_values_written_as_iso_strings(tmp_path, cls, ext, bulk):
    rows = _roundtrip(cls, tmp_path / f"times.{ext}", bulk)
    assert len(rows) == 1
    assert rows[0]["t"] == "10:30:00"
    assert rows[0]["t_us"] == "10:30:00.000123"
    assert rows[0]["d"] == "2024-01-02"
