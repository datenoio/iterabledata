"""Write-support tests for the ODS format (OpenSpec add-office-format-writes)."""

import importlib.util

import pytest

from iterable import open_iterable

pytestmark = pytest.mark.skipif(importlib.util.find_spec("odf") is None, reason="odfpy not installed")


class TestODSWrite:
    def test_write_and_read_roundtrip(self, tmp_path):
        path = tmp_path / "out.ods"
        records = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
        with open_iterable(str(path), mode="w") as target:
            for record in records:
                target.write(record)
        with open_iterable(str(path)) as source:
            rows = list(source)
        # The reader yields cell text content.
        assert rows == [{"a": "1", "b": "x"}, {"a": "2", "b": "y"}]

    def test_write_bulk(self, tmp_path):
        path = tmp_path / "bulk.ods"
        with open_iterable(str(path), mode="w") as target:
            target.write_bulk([{"n": 1}, {"n": 2}, {"n": 3}])
        with open_iterable(str(path)) as source:
            assert len(list(source)) == 3

    def test_typed_cells_loadable_by_odfpy(self, tmp_path):
        from odf.opendocument import load
        from odf.table import Table, TableCell

        path = tmp_path / "typed.ods"
        with open_iterable(str(path), mode="w") as target:
            target.write({"i": 7, "f": 2.5, "b": True, "s": "txt"})
        doc = load(str(path))
        cells = doc.spreadsheet.getElementsByType(Table)[0].getElementsByType(TableCell)
        by_type = {}
        for cell in cells:
            valuetype = cell.getAttribute("valuetype")
            if valuetype in ("float", "boolean"):
                by_type.setdefault(valuetype, []).append(cell)
        assert any(str(c.getAttribute("value")) == "7" for c in by_type["float"])
        assert any(str(c.getAttribute("value")) == "2.5" for c in by_type["float"])
        assert any(str(c.getAttribute("booleanvalue")) == "true" for c in by_type["boolean"])

    def test_header_extends_with_late_keys(self, tmp_path):
        path = tmp_path / "late.ods"
        with open_iterable(str(path), mode="w") as target:
            target.write({"a": 1})
            target.write({"a": 2, "b": "new"})
        with open_iterable(str(path)) as source:
            rows = list(source)
        assert rows == [{"a": "1", "b": ""}, {"a": "2", "b": "new"}]

    def test_validation_hook_skip(self, tmp_path):
        path = tmp_path / "validated.ods"

        def reject_negative(row):
            if row.get("n", 0) < 0:
                raise ValueError("negative")
            return row

        with open_iterable(
            str(path), mode="w", iterableargs={"validation_hook": reject_negative, "on_validation_error": "skip"}
        ) as target:
            target.write({"n": 1})
            target.write({"n": -5})
        with open_iterable(str(path)) as source:
            assert list(source) == [{"n": "1"}]

    def test_write_bulk_none_raises(self, tmp_path):
        path = tmp_path / "none.ods"
        with open_iterable(str(path), mode="w") as target:
            with pytest.raises(TypeError):
                target.write_bulk(None)
