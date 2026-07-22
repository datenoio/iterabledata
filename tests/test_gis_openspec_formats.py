"""Tests for OpenSpec GIS / grid / LiDAR format modules."""

from __future__ import annotations

from pathlib import Path

import pytest

from iterable.datatypes.asciigrid import ASCIIGridIterable
from iterable.datatypes.czml import CZMLIterable
from iterable.datatypes.e00 import E00Iterable
from iterable.exceptions import WriteNotSupportedError

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class TestASCIIGrid:
    def test_id(self):
        assert ASCIIGridIterable.id() == "asc"

    def test_read_cell_mode_skips_nodata(self):
        path = FIXTURES / "sample.asc"
        with ASCIIGridIterable(str(path)) as source:
            rows = list(source)
        # 3x3 with one nodata -> 8 cells
        assert len(rows) == 8
        assert rows[0] == {"row": 0, "col": 0, "x": 0.5, "y": 2.5, "value": 1.0}
        nodata_cells = [r for r in rows if r["row"] == 1 and r["col"] == 1]
        assert nodata_cells == []

    def test_read_row_mode(self):
        path = FIXTURES / "sample.asc"
        with ASCIIGridIterable(str(path), options={"mode": "row"}) as source:
            rows = list(source)
        assert len(rows) == 3
        assert rows[1] == {"row": 1, "values": [4.0, -9999.0, 6.0]}

    def test_write_cell_roundtrip(self, tmp_path):
        out = tmp_path / "out.asc"
        cells = [
            {"row": 0, "col": 0, "x": 0.5, "y": 1.5, "value": 10.0},
            {"row": 0, "col": 1, "x": 1.5, "y": 1.5, "value": 20.0},
            {"row": 1, "col": 0, "x": 0.5, "y": 0.5, "value": 30.0},
            {"row": 1, "col": 1, "x": 1.5, "y": 0.5, "value": 40.0},
        ]
        with ASCIIGridIterable(str(out), mode="w") as dest:
            dest.write_bulk(cells)
        with ASCIIGridIterable(str(out)) as source:
            got = list(source)
        assert len(got) == 4
        assert {c["value"] for c in got} == {10.0, 20.0, 30.0, 40.0}

    def test_read_bulk_empty_at_end(self):
        path = FIXTURES / "sample.asc"
        with ASCIIGridIterable(str(path)) as source:
            first = source.read_bulk(100)
            assert len(first) == 8
            assert source.read_bulk(10) == []


class TestCZML:
    def test_id(self):
        assert CZMLIterable.id() == "czml"

    def test_read_packets(self):
        path = FIXTURES / "sample.czml"
        with CZMLIterable(str(path)) as source:
            packets = list(source)
        assert len(packets) == 2
        assert packets[0]["id"] == "document"
        assert packets[1]["id"] == "point-1"

    def test_write_roundtrip(self, tmp_path):
        out = tmp_path / "out.czml"
        packets = [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}]
        with CZMLIterable(str(out), mode="w") as dest:
            dest.write_bulk(packets)
        with CZMLIterable(str(out)) as source:
            assert list(source) == packets

    def test_single_object(self, tmp_path):
        path = tmp_path / "one.czml"
        path.write_text('{"id": "solo", "version": "1.0"}\n', encoding="utf-8")
        with CZMLIterable(str(path)) as source:
            packets = list(source)
        assert packets == [{"id": "solo", "version": "1.0"}]


class TestE00:
    def test_id(self):
        assert E00Iterable.id() == "e00"

    def test_read_arc_and_lab(self):
        path = FIXTURES / "sample.e00"
        with E00Iterable(str(path)) as source:
            rows = list(source)
        types = [r["type"] for r in rows]
        assert "ARC" in types
        assert "LAB" in types
        arc = next(r for r in rows if r["type"] == "ARC")
        assert arc["id"] == 1
        assert len(arc["coordinates"]) == 2
        lab = next(r for r in rows if r["type"] == "LAB")
        assert lab["id"] == 1
        assert lab["x"] == 0.5

    def test_unsupported_section(self, tmp_path):
        path = tmp_path / "bad.e00"
        path.write_text("EXP  0\nIFO  2\nsome data\nEOI\nEOS\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported E00 section"):
            with E00Iterable(str(path)) as source:
                list(source)

    def test_write_not_supported(self, tmp_path):
        path = tmp_path / "out.e00"
        with pytest.raises(WriteNotSupportedError):
            E00Iterable(str(path), mode="w")


class TestFileGDB:
    def test_id_and_import(self):
        fiona = pytest.importorskip("fiona")
        from iterable.datatypes.filegdb import FileGDBIterable

        assert FileGDBIterable.id() == "fgdb"
        assert FileGDBIterable.has_tables() is True
        with pytest.raises(WriteNotSupportedError):
            FileGDBIterable("missing.gdb", mode="w")
        # Driver may or may not be present; just ensure ImportError path is not hit
        assert fiona is not None


class TestMapInfo:
    def test_id_and_readonly(self):
        pytest.importorskip("fiona")
        from iterable.datatypes.mif import MapInfoIterable

        assert MapInfoIterable.id() == "mif"
        with pytest.raises(WriteNotSupportedError):
            MapInfoIterable("missing.mif", mode="w")


class TestLAS:
    def test_id_and_import_message(self):
        laspy = pytest.importorskip("laspy")
        from iterable.datatypes.las import LASIterable

        assert LASIterable.id() == "las"
        assert laspy is not None
        with pytest.raises(WriteNotSupportedError):
            LASIterable("missing.las", mode="w")


class TestBAG:
    def test_id_and_list_tables(self, tmp_path):
        h5py = pytest.importorskip("h5py")
        import numpy as np

        from iterable.datatypes.bag import BAGIterable

        assert BAGIterable.id() == "bag"
        assert BAGIterable.has_tables() is True

        path = tmp_path / "sample.bag"
        with h5py.File(path, "w") as f:
            root = f.create_group("BAG_root")
            root.create_dataset("elevation", data=np.array([[1.0, 2.0], [3.0, 4.0]]))
            root.create_dataset("uncertainty", data=np.array([[0.1, 0.2], [0.3, 0.4]]))

        with BAGIterable(str(path)) as source:
            tables = source.list_tables()
            assert "/BAG_root/elevation" in tables
            assert "/BAG_root/uncertainty" in tables
            rows = list(source)
        assert len(rows) == 4
        assert rows[0] == {"row": 0, "col": 0, "value": 1.0}
        assert rows[-1] == {"row": 1, "col": 1, "value": 4.0}

        with BAGIterable(str(path), options={"dataset": "/BAG_root/uncertainty"}) as source:
            rows = list(source)
        assert rows[0]["value"] == pytest.approx(0.1)

        with pytest.raises(WriteNotSupportedError):
            BAGIterable(str(path), mode="w")
