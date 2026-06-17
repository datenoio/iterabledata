"""Tests for formats that previously lacked dedicated coverage (plan item 4.1)."""

from __future__ import annotations

import zipfile

import pytest

from iterable.datatypes.zipped import ZIPSourceWrapper
from iterable.exceptions import FormatNotSupportedError
from iterable.helpers.detect import DATATYPE_REGISTRY, _load_symbol

# Canonical registry keys for the ten previously uncovered formats.
UNCOVERED_FORMAT_KEYS = (
    "kafka",
    "pulsar",
    "flink",
    "beam",
    "lance",
    "recordio",
    "sequencefile",
    "tfrecord",
    "flexbuffers",
)

ROUND_TRIP_FORMATS = (
    "tfrecord",
    "recordio",
    "kafka",
    "pulsar",
    "flink",
    "beam",
)

SAMPLE_ROWS = [
    {"key": "k1", "value": {"id": 1, "name": "alpha"}},
    {"key": "k2", "value": {"id": 2, "name": "beta"}},
]


def _load_class(format_key: str):
    module_path, symbol = DATATYPE_REGISTRY[format_key]
    try:
        return _load_symbol(module_path, symbol)
    except ImportError as exc:
        pytest.skip(f"Optional dependency missing for {format_key!r}: {exc}")


def _read_all(source) -> list[dict]:
    rows: list[dict] = []
    while True:
        try:
            rows.append(source.read())
        except StopIteration:
            break
    return rows


def _assert_key_value_roundtrip(original: list[dict], read_back: list[dict]) -> None:
    assert len(read_back) == len(original)
    for expected, actual in zip(original, read_back, strict=True):
        assert actual["key"] == expected["key"]
        assert actual["value"] == expected["value"]


class TestUncoveredFormatRegistry:
    @pytest.mark.parametrize("format_key", UNCOVERED_FORMAT_KEYS)
    def test_class_loads_and_exposes_static_id(self, format_key: str):
        cls = _load_class(format_key)
        format_id = cls.id()
        assert isinstance(format_id, str) and format_id

    @pytest.mark.parametrize("format_key", UNCOVERED_FORMAT_KEYS)
    def test_iterator_contract_methods_present(self, format_key: str):
        cls = _load_class(format_key)
        for method in ("read", "read_bulk", "reset"):
            assert callable(getattr(cls, method, None))


class TestUncoveredFormatRoundTrip:
    @pytest.mark.parametrize("format_key", ROUND_TRIP_FORMATS)
    def test_write_read_roundtrip(self, format_key: str, tmp_path):
        cls = _load_class(format_key)
        target = tmp_path / f"sample.{format_key}"

        with cls(str(target), mode="w") as dest:
            dest.write_bulk(SAMPLE_ROWS)

        with cls(str(target), mode="r") as source:
            read_back = _read_all(source)

        _assert_key_value_roundtrip(SAMPLE_ROWS, read_back)


class TestSequenceFileReadContract:
    def test_write_then_read_yields_no_rows_without_header(self, tmp_path):
        """Document current SequenceFile behavior: files written without a header do not read back."""
        cls = _load_class("sequencefile")
        target = tmp_path / "sample.seq"

        with cls(str(target), mode="w") as dest:
            dest.write({"key": "k1", "value": {"id": 1}})

        with cls(str(target), mode="r") as source:
            assert _read_all(source) == []


class TestFlexBuffersRoundTrip:
    def test_write_read_single_record(self, tmp_path):
        pytest.importorskip("flexbuffers")
        cls = _load_class("flexbuffers")
        target = tmp_path / "sample.flexbuf"

        with cls(str(target), mode="w") as dest:
            dest.write({"id": 1, "name": "alpha"})

        with cls(str(target), mode="r") as source:
            row = source.read()
            with pytest.raises(StopIteration):
                source.read()

        assert row == {"id": 1, "name": "alpha"}


class TestLanceImport:
    def test_lance_requires_optional_dependency(self):
        pytest.importorskip("lance")
        cls = _load_class("lance")
        assert cls.id() == "lance"


class TestZippedWrapper:
    def test_id_reset_and_close(self, tmp_path):
        archive = tmp_path / "archive.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("a.txt", "hello\n")

        source = ZIPSourceWrapper(str(archive))
        try:
            assert source.id() == "zipped"
            source.reset()
            assert source.filenum == 0
        finally:
            source.close()

    def test_read_single_is_not_supported(self, tmp_path):
        archive = tmp_path / "archive.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("a.txt", "hello\n")

        source = ZIPSourceWrapper(str(archive))
        try:
            with pytest.raises(FormatNotSupportedError):
                source.read_single()
        finally:
            source.close()
