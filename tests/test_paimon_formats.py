"""Tests for Apache Paimon Row and Mosaic format support."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from iterable.helpers.content_detection import detect_file_type_from_content
from iterable.helpers.detect import open_iterable
from iterable.helpers.format_registry import get_descriptor, install_extra_hint

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCHEMA = [("id", "bigint"), ("name", "string"), ("score", "double")]
RECORDS = [
    {"id": 1, "name": "Alice", "score": 1.5},
    {"id": 2, "name": "Bob", "score": 2.25},
    {"id": 3, "name": "Carol", "score": None},
]


class TestPaimonRowRegistry:
    def test_descriptor(self):
        desc = get_descriptor("paimon_row")
        assert desc is not None
        assert desc.cls == "PaimonRowIterable"
        assert desc.maturity == "experimental"
        assert desc.write_memory == "bounded"
        assert get_descriptor("row") is desc

    def test_install_hint(self):
        assert install_extra_hint("iterable.datatypes.paimon_row") == "paimon-row"


class TestPaimonRow:
    def test_missing_schema_raises(self, tmp_path):
        path = tmp_path / "noschema.row"
        with open_iterable(str(path), mode="w", iterableargs={"schema": SCHEMA}) as dest:
            dest.write_bulk(RECORDS)
        with pytest.raises(ValueError, match="explicit schema"):
            open_iterable(str(path))

    def test_round_trip(self, tmp_path):
        path = tmp_path / "people.row"
        with open_iterable(str(path), mode="w", iterableargs={"schema": SCHEMA, "block_size": 64}) as dest:
            dest.write_bulk(RECORDS)
        with open_iterable(str(path), iterableargs={"schema": SCHEMA}) as source:
            assert source.totals() == 3
            rows = list(source)
        assert rows == RECORDS
        with open_iterable(str(path), iterableargs={"schema": SCHEMA}) as source:
            source.reset()
            assert source.read()["name"] == "Alice"
            bulk = source.read_bulk(10)
            assert len(bulk) == 2

    def test_infer_schema_on_write(self, tmp_path):
        path = tmp_path / "infer.row"
        with open_iterable(str(path), mode="w") as dest:
            dest.write({"id": 7, "name": "Dee"})
        with open_iterable(str(path), iterableargs={"schema": [("id", "bigint"), ("name", "string")]}) as source:
            assert list(source) == [{"id": 7, "name": "Dee"}]

    def test_footer_magic_detection(self, tmp_path):
        path = tmp_path / "detect.bin"
        with open_iterable(str(path), mode="w", iterableargs={"format": "paimon_row", "schema": SCHEMA}) as dest:
            dest.write_bulk(RECORDS[:1])
        with open(path, "rb") as f:
            detected = detect_file_type_from_content(f)
        assert detected is not None
        assert detected[0] == "paimon_row"
        assert detected[2] == "magic_number"

    def test_extension_detection(self, tmp_path):
        path = tmp_path / "ext.row"
        with open_iterable(str(path), mode="w", iterableargs={"schema": SCHEMA}) as dest:
            dest.write_bulk(RECORDS[:1])
        with open_iterable(str(path), iterableargs={"schema": SCHEMA}) as source:
            assert source.id() == "paimon_row"
            assert list(source)[0]["id"] == 1

    def test_malformed_footer(self, tmp_path):
        path = tmp_path / "bad.row"
        path.write_bytes(b"not-a-row-file" + b"\x00" * 20 + b"XXXX")
        with pytest.raises(ValueError):
            with open_iterable(str(path), iterableargs={"schema": SCHEMA}) as source:
                list(source)

    def test_missing_dependency_message(self, monkeypatch):
        import iterable.datatypes.paimon_row as mod

        monkeypatch.setattr(mod, "HAS_ZSTD", False)
        with pytest.raises(ImportError, match="paimon-row"):
            mod.PaimonRowIterable(filename="x.row", mode="w")

    def test_committed_fixture_round_trip(self):
        fixture = FIXTURES / "2cols3rows.row"
        if not fixture.exists():
            pytest.skip("fixture not generated yet")
        schema = [("id", "bigint"), ("name", "string")]
        with open_iterable(str(fixture), iterableargs={"schema": schema}) as source:
            rows = list(source)
        assert len(rows) == 3
        assert rows[0]["name"] == "a"


mosaic = pytest.importorskip("mosaic", reason="paimon-mosaic package not installed")


class TestPaimonMosaicRegistry:
    def test_descriptor(self):
        desc = get_descriptor("paimon_mosaic")
        assert desc is not None
        assert desc.cls == "PaimonMosaicIterable"
        assert desc.maturity == "experimental"
        assert get_descriptor("mosaic") is desc

    def test_install_hint(self):
        assert install_extra_hint("iterable.datatypes.paimon_mosaic") == "paimon-mosaic"


class TestPaimonMosaic:
    def test_round_trip(self, tmp_path):
        path = tmp_path / "wide.mosaic"
        with open_iterable(str(path), mode="w", iterableargs={"num_buckets": 2}) as dest:
            dest.write_bulk(RECORDS)
        with open_iterable(str(path)) as source:
            assert source.totals() == 3
            rows = list(source)
        assert [r["name"] for r in rows] == ["Alice", "Bob", "Carol"]
        assert rows[2]["score"] is None

    def test_projection(self, tmp_path):
        path = tmp_path / "proj.mosaic"
        with open_iterable(str(path), mode="w") as dest:
            dest.write_bulk(RECORDS)
        with open_iterable(str(path), iterableargs={"columns": ["name"]}) as source:
            rows = list(source)
        assert rows == [{"name": "Alice"}, {"name": "Bob"}, {"name": "Carol"}]

    def test_footer_magic_detection(self, tmp_path):
        path = tmp_path / "detect.mosaic"
        with open_iterable(str(path), mode="w") as dest:
            dest.write_bulk(RECORDS[:1])
        # Rename to hide extension
        bare = tmp_path / "detect.bin"
        os.rename(path, bare)
        with open(bare, "rb") as f:
            detected = detect_file_type_from_content(f)
        assert detected is not None
        assert detected[0] == "paimon_mosaic"

    def test_missing_dependency_message(self, monkeypatch):
        import iterable.datatypes.paimon_mosaic as mod

        monkeypatch.setattr(mod, "HAS_MOSAIC", False)
        with pytest.raises(ImportError, match="paimon-mosaic"):
            mod.PaimonMosaicIterable(filename="x.mosaic", mode="w")

    def test_committed_fixture(self):
        fixture = FIXTURES / "2cols3rows.mosaic"
        if not fixture.exists():
            pytest.skip("fixture not generated yet")
        with open_iterable(str(fixture)) as source:
            rows = list(source)
        assert len(rows) == 3
