"""Convert-pipeline round-trips for office formats (OpenSpec add-office-format-writes)."""

import importlib.util

import pytest

from iterable import open_iterable
from iterable.convert import convert

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("openpyxl") is None or importlib.util.find_spec("odf") is None,
    reason="openpyxl and odfpy required",
)


def _write(path, records, **kwargs):
    with open_iterable(str(path), mode="w", **kwargs) as target:
        target.write_bulk(records)


def _read(path, **kwargs):
    with open_iterable(str(path), **kwargs) as source:
        return list(source)


class TestOfficeConvertRoundTrips:
    def test_csv_xlsx_csv(self, tmp_path):
        records = [{"a": "1", "b": "x"}, {"a": "2", "b": "y"}]
        csv_in = tmp_path / "in.csv"
        xlsx = tmp_path / "mid.xlsx"
        csv_out = tmp_path / "out.csv"
        _write(csv_in, records)
        convert(str(csv_in), str(xlsx))
        convert(str(xlsx), str(csv_out))
        assert _read(csv_out) == records

    def test_jsonl_xml_jsonl(self, tmp_path):
        records = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
        jsonl_in = tmp_path / "in.jsonl"
        xml = tmp_path / "mid.xml"
        jsonl_out = tmp_path / "out.jsonl"
        _write(jsonl_in, records)
        convert(str(jsonl_in), str(xml), toiterableargs={"tagname": "item"})
        convert(str(xml), str(jsonl_out), iterableargs={"tagname": "item"})
        assert _read(jsonl_out) == [{"a": "1", "b": "x"}, {"a": "2", "b": "y"}]

    def test_csv_ods_csv(self, tmp_path):
        records = [{"a": "1", "b": "x"}, {"a": "2", "b": "y"}]
        csv_in = tmp_path / "in.csv"
        ods = tmp_path / "mid.ods"
        csv_out = tmp_path / "out.csv"
        _write(csv_in, records)
        convert(str(csv_in), str(ods))
        convert(str(ods), str(csv_out))
        assert _read(csv_out) == records
