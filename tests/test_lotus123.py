"""Behavior tests for the Lotus 1-2-3 (WK1) reader.

Pins the observable behavior of ``iterable.datatypes.lotus123._parse_wk1``
(and the ``Lotus123Iterable`` wrapper) for the complexity refactor: record
parsing (LABEL / INTEGER / NUMBER), header-row detection, column-letter
fallback keys, empty-row skipping, and error paths. Uses the committed
``fixtures/sample.wk1`` plus synthetic in-memory WK1 byte streams.
"""

import struct

import pytest

from iterable.datatypes.lotus123 import Lotus123Iterable, _col_name, _parse_wk1
from iterable.exceptions import FormatParseError, WriteNotSupportedError

FIXTURE = "fixtures/sample.wk1"

# WK1 opcodes (mirror iterable.datatypes.lotus123 internals)
_BOF = 0x0000
_EOF = 0x0001
_INTEGER = 0x000D
_NUMBER = 0x000E
_LABEL = 0x000F


def _record(opcode: int, body: bytes) -> bytes:
    return struct.pack("<HH", opcode, len(body)) + body


def _label(col: int, row: int, text: str, align: bytes = b"'") -> bytes:
    return _record(_LABEL, struct.pack("<Bhh", 0xFF, col, row) + align + text.encode("latin-1") + b"\x00")


def _integer(col: int, row: int, value: int) -> bytes:
    return _record(_INTEGER, struct.pack("<Bhhh", 0xFF, col, row, value))


def _number(col: int, row: int, value: float) -> bytes:
    return _record(_NUMBER, struct.pack("<Bhh", 0xFF, col, row) + struct.pack("<d", value))


def _wk1(*records: bytes, bof: bytes = b"\x04\x04", eof: bool = True) -> bytes:
    parts = [_record(_BOF, bof), *records]
    if eof:
        parts.append(_record(_EOF, b""))
    return b"".join(parts)


class TestColName:
    def test_first_columns(self):
        assert _col_name(0) == "A"
        assert _col_name(1) == "B"
        assert _col_name(25) == "Z"

    def test_double_letter_columns(self):
        assert _col_name(26) == "AA"
        assert _col_name(27) == "AB"


class TestFixture:
    def test_sample_wk1_rows(self):
        with open(FIXTURE, "rb") as f:
            rows = _parse_wk1(f.read())
        assert rows == [{"name": "alpha", "value": 42}, {"name": "beta", "value": 3.5}]


class TestRecordParsing:
    def test_integer_cell_type(self):
        rows = _parse_wk1(_wk1(_integer(0, 0, 7)))
        assert rows == [{"A": 7}]
        assert isinstance(rows[0]["A"], int)

    def test_number_cell_type(self):
        rows = _parse_wk1(_wk1(_number(0, 0, 2.5)))
        assert rows == [{"A": 2.5}]
        assert isinstance(rows[0]["A"], float)

    def test_later_record_overwrites_same_cell(self):
        """Two records addressing the same (row, col): the last write wins."""
        rows = _parse_wk1(_wk1(_integer(0, 0, 1), _integer(0, 0, 5)))
        assert rows == [{"A": 5}]

    def test_label_without_alignment_prefix_kept(self):
        """A label whose first byte is not an alignment char keeps the byte."""
        body = struct.pack("<Bhh", 0xFF, 0, 0) + b"hi\x00"
        rows = _parse_wk1(_wk1(_record(_LABEL, body), _integer(0, 1, 1)))
        assert rows == [{"hi": 1}]

    def test_label_alignment_variants_stripped(self):
        for align in (b"'", b'"', b"^", b"\\"):
            rows = _parse_wk1(_wk1(_label(0, 0, "v", align=align), _integer(0, 1, 1)))
            assert rows == [{"v": 1}]

    def test_unknown_opcodes_ignored(self):
        blob = _wk1(_record(0x0064, b"\x01\x02\x03\x04"), _integer(0, 0, 3))
        assert _parse_wk1(blob) == [{"A": 3}]


class TestHeaderDetection:
    def test_all_label_row_zero_becomes_header(self):
        rows = _parse_wk1(_wk1(_label(0, 0, "name"), _label(1, 0, "value"), _label(0, 1, "a"), _integer(1, 1, 9)))
        assert rows == [{"name": "a", "value": 9}]

    def test_numeric_row_zero_means_no_header(self):
        rows = _parse_wk1(_wk1(_integer(0, 0, 1), _integer(0, 1, 2)))
        assert rows == [{"A": 1}, {"A": 2}]

    def test_empty_header_cells_fall_back_to_letters(self):
        """Blank label cells in the header row use the column letter."""
        rows = _parse_wk1(_wk1(_label(0, 0, "x"), _label(1, 0, ""), _label(0, 1, "a"), _integer(1, 1, 4)))
        assert rows == [{"x": "a", "B": 4}]

    def test_gap_in_header_columns_falls_back_to_letters(self):
        """A missing (None) header cell uses the column letter."""
        rows = _parse_wk1(_wk1(_label(1, 0, "b"), _integer(0, 1, 8), _integer(1, 1, 9)))
        assert rows == [{"A": 8, "b": 9}]

    def test_completely_empty_rows_skipped(self):
        rows = _parse_wk1(_wk1(_integer(0, 0, 1), _integer(0, 2, 3)))
        assert rows == [{"A": 1}, {"A": 3}]


class TestErrors:
    def test_empty_data_raises(self):
        with pytest.raises(FormatParseError):
            _parse_wk1(b"")

    def test_short_data_raises(self):
        with pytest.raises(FormatParseError):
            _parse_wk1(b"\x00\x00\x00")

    def test_truncated_record_raises(self):
        blob = _record(_BOF, b"\x04\x04") + struct.pack("<HH", _LABEL, 20) + b"\xff\x00"
        with pytest.raises(FormatParseError):
            _parse_wk1(blob)

    def test_no_bof_and_no_cells_raises(self):
        with pytest.raises(FormatParseError):
            _parse_wk1(_record(0x0064, b"\x01\x02"))

    def test_bof_only_returns_empty(self):
        assert _parse_wk1(_wk1()) == []

    def test_bof_without_eof_returns_rows(self):
        """EOF is optional: running out of bytes ends the record loop."""
        rows = _parse_wk1(_wk1(_integer(0, 0, 11), eof=False))
        assert rows == [{"A": 11}]

    def test_cells_without_bof_accepted(self):
        """Cells alone (no BOF) still parse — the error needs both missing."""
        blob = _record(_INTEGER, struct.pack("<Bhhh", 0xFF, 0, 0, 6))
        assert _parse_wk1(blob) == [{"A": 6}]


class TestIterableIntegration:
    def test_read_fixture(self):
        iterable = Lotus123Iterable(FIXTURE)
        try:
            assert list(iterable) == [{"name": "alpha", "value": 42}, {"name": "beta", "value": 3.5}]
        finally:
            iterable.close()

    def test_read_garbage_raises(self, tmp_path):
        path = tmp_path / "bad.wk1"
        path.write_bytes(b"not a wk1 file at all")
        with pytest.raises(FormatParseError):
            Lotus123Iterable(str(path))

    def test_write_not_supported(self, tmp_path):
        iterable = Lotus123Iterable(FIXTURE)
        try:
            with pytest.raises(WriteNotSupportedError):
                iterable.write({"a": 1})
            with pytest.raises(WriteNotSupportedError):
                iterable.write_bulk([{"a": 1}])
        finally:
            iterable.close()

    def test_write_mode_rejected(self, tmp_path):
        path = tmp_path / "out.wk1"
        with pytest.raises(WriteNotSupportedError):
            Lotus123Iterable(str(path), mode="w")

    def test_is_flatonly_and_id(self):
        assert Lotus123Iterable.id() == "123"
        assert Lotus123Iterable.is_flatonly() is True
