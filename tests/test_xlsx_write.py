"""Write-support tests for the XLSX format (OpenSpec add-office-format-writes)."""

import datetime

import pytest

from iterable import open_iterable

load_workbook = pytest.importorskip("openpyxl", reason="openpyxl is required for XLSX support").load_workbook


class TestXLSXWrite:
    def test_write_and_read_roundtrip(self, tmp_path):
        path = tmp_path / "out.xlsx"
        records = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
        with open_iterable(str(path), mode="w") as target:
            for record in records:
                target.write(record)
        with open_iterable(str(path)) as source:
            rows = list(source)
        # The reader stringifies cell values.
        assert rows == [{"a": "1", "b": "x"}, {"a": "2", "b": "y"}]

    def test_write_bulk(self, tmp_path):
        path = tmp_path / "bulk.xlsx"
        with open_iterable(str(path), mode="w") as target:
            target.write_bulk([{"n": 1}, {"n": 2}, {"n": 3}])
        with open_iterable(str(path)) as source:
            assert len(list(source)) == 3

    def test_header_extends_with_late_keys(self, tmp_path):
        path = tmp_path / "late.xlsx"
        with open_iterable(str(path), mode="w") as target:
            target.write({"a": 1})
            target.write({"a": 2, "b": "new"})
        workbook = load_workbook(str(path))
        sheet = workbook.active
        values = [[cell.value for cell in row] for row in sheet.iter_rows()]
        assert values[0] == ["a", "b"]
        assert values[1] == [1, None]
        assert values[2] == [2, "new"]
        workbook.close()

    def test_typed_cells_preserved_for_openpyxl(self, tmp_path):
        path = tmp_path / "typed.xlsx"
        when = datetime.datetime(2026, 9, 27, 12, 30)
        with open_iterable(str(path), mode="w") as target:
            target.write({"i": 7, "f": 2.5, "b": True, "s": "txt", "d": when, "z": None})
        workbook = load_workbook(str(path))
        sheet = workbook.active
        rows = list(sheet.iter_rows(values_only=True))
        assert rows[1] == (7, 2.5, True, "txt", when, None)
        workbook.close()

    def test_non_scalar_values_are_stringified(self, tmp_path):
        path = tmp_path / "flat.xlsx"
        with open_iterable(str(path), mode="w") as target:
            target.write({"a": [1, 2], "b": {"x": 1}})
        workbook = load_workbook(str(path))
        sheet = workbook.active
        rows = list(sheet.iter_rows(values_only=True))
        assert rows[1] == ("[1, 2]", "{'x': 1}")
        workbook.close()

    def test_validation_hook_skip(self, tmp_path):
        path = tmp_path / "validated.xlsx"

        def reject_negative(row):
            if row.get("n", 0) < 0:
                raise ValueError("negative")
            return row

        with open_iterable(
            str(path), mode="w", iterableargs={"validation_hook": reject_negative, "on_validation_error": "skip"}
        ) as target:
            target.write({"n": 1})
            target.write({"n": -5})
            target.write({"n": 3})
        with open_iterable(str(path)) as source:
            rows = list(source)
        assert rows == [{"n": "1"}, {"n": "3"}]

    def test_write_bulk_none_raises(self, tmp_path):
        path = tmp_path / "none.xlsx"
        with open_iterable(str(path), mode="w") as target:
            with pytest.raises(TypeError):
                target.write_bulk(None)

    def test_empty_write_produces_valid_workbook(self, tmp_path):
        path = tmp_path / "empty.xlsx"
        with open_iterable(str(path), mode="w"):
            pass
        workbook = load_workbook(str(path))
        assert workbook.sheetnames
        workbook.close()
