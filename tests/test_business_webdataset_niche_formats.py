"""Tests for business exchange, WebDataset, and niche RDF/stats formats.

Imports format classes directly (registry wiring is out of scope for this change).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from iterable.datatypes.edi import EDIIterable
from iterable.datatypes.fst import HAS_FST, FSTIterable
from iterable.datatypes.hdt import HAS_HDT, HDTIterable
from iterable.datatypes.iati import HAS_LXML, IATIIterable
from iterable.datatypes.lotus123 import Lotus123Iterable
from iterable.datatypes.mdb import HAS_ACCESS_PARSER, HAS_PYODBC, AccessMDBIterable
from iterable.datatypes.webdataset import WebDatasetIterable
from iterable.exceptions import FormatParseError, WriteNotSupportedError

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class TestEDI:
    def test_id(self):
        assert EDIIterable.id() == "edi"

    def test_read_segments(self):
        path = FIXTURES / "sample.edi"
        with EDIIterable(filename=str(path)) as src:
            rows = list(src)
        assert len(rows) >= 5
        assert rows[0]["segment_id"] == "ISA"
        assert isinstance(rows[0]["elements"], list)
        assert any(r["segment_id"] == "BEG" for r in rows)
        beg = next(r for r in rows if r["segment_id"] == "BEG")
        assert "PO123" in beg["elements"]

    def test_write_not_supported(self):
        path = FIXTURES / "sample.edi"
        with EDIIterable(filename=str(path)) as src:
            with pytest.raises(WriteNotSupportedError):
                src.write({"segment_id": "ISA", "elements": []})

    def test_reset(self):
        path = FIXTURES / "sample.edi"
        with EDIIterable(filename=str(path)) as src:
            first = src.read()
            src.reset()
            assert src.read() == first


class TestLotus123:
    def test_id(self):
        assert Lotus123Iterable.id() == "123"

    def test_read_wk1(self):
        path = FIXTURES / "sample.wk1"
        with Lotus123Iterable(filename=str(path)) as src:
            rows = list(src)
        assert len(rows) == 2
        assert rows[0]["name"] == "alpha"
        assert rows[0]["value"] == 42
        assert rows[1]["name"] == "beta"
        assert rows[1]["value"] == pytest.approx(3.5)

    def test_write_not_supported(self):
        path = FIXTURES / "sample.wk1"
        with Lotus123Iterable(filename=str(path)) as src:
            with pytest.raises(WriteNotSupportedError):
                src.write({"A": 1})


class TestWebDataset:
    def test_id(self):
        assert WebDatasetIterable.id() == "webdataset"

    def test_read_samples(self):
        path = FIXTURES / "sample_webdataset.tar"
        with WebDatasetIterable(filename=str(path)) as src:
            samples = list(src)
        assert len(samples) == 2
        assert samples[0]["__key__"] == "sample1"
        assert samples[0]["json"] == {"label": "cat"}
        assert samples[0]["txt"] == "a cat"
        assert isinstance(samples[0]["jpg"], (bytes, bytearray))
        assert samples[1]["__key__"] == "sample2"
        assert samples[1]["json"]["label"] == "dog"

    def test_partial_group_error(self, tmp_path):
        import io
        import json
        import tarfile

        path = tmp_path / "partial.tar"
        with tarfile.open(path, "w") as tar:
            for name, data in (
                ("a.json", json.dumps({"x": 1}).encode()),
                ("a.txt", b"full"),
                ("b.json", json.dumps({"x": 2}).encode()),
                # missing b.txt → incomplete trailing group
            ):
                info = tarfile.TarInfo(name=name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))

        with pytest.raises(FormatParseError, match="Incomplete trailing"):
            WebDatasetIterable(filename=str(path))

    def test_partial_group_yield(self, tmp_path):
        import io
        import json
        import tarfile

        path = tmp_path / "partial_yield.tar"
        with tarfile.open(path, "w") as tar:
            for name, data in (
                ("a.json", json.dumps({"x": 1}).encode()),
                ("a.txt", b"full"),
                ("b.json", json.dumps({"x": 2}).encode()),
            ):
                info = tarfile.TarInfo(name=name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))

        with WebDatasetIterable(filename=str(path), options={"partial_group": "yield"}) as src:
            samples = list(src)
        assert len(samples) == 2
        assert samples[1]["__key__"] == "b"
        assert "txt" not in samples[1]

    def test_write_not_supported(self):
        path = FIXTURES / "sample_webdataset.tar"
        with WebDatasetIterable(filename=str(path)) as src:
            with pytest.raises(WriteNotSupportedError):
                src.write({"__key__": "x"})


class TestMDB:
    def test_id(self):
        assert AccessMDBIterable.id() == "mdb"

    def test_missing_dependency_message(self):
        if HAS_ACCESS_PARSER or HAS_PYODBC:
            pytest.skip("Access backend is installed")
        with pytest.raises(ImportError, match="iterabledata\\[access\\]"):
            AccessMDBIterable(filename="missing.mdb")


@pytest.mark.skipif(not HAS_FST, reason="fst/rfst binding not installed")
class TestFST:
    def test_id(self):
        assert FSTIterable.id() == "fst"


class TestFSTMissing:
    def test_import_error_when_missing(self):
        if HAS_FST:
            pytest.skip("fst binding is installed")
        with pytest.raises(ImportError, match="fst"):
            FSTIterable(filename="x.fst")


@pytest.mark.skipif(not HAS_HDT, reason="hdt package not installed")
class TestHDT:
    def test_id(self):
        assert HDTIterable.id() == "hdt"


class TestHDTMissing:
    def test_import_error_when_missing(self):
        if HAS_HDT:
            pytest.skip("hdt is installed")
        with pytest.raises(ImportError, match="hdt"):
            HDTIterable(filename="x.hdt")


@pytest.mark.skipif(not HAS_LXML, reason="lxml not installed")
class TestIATI:
    def test_id(self):
        assert IATIIterable.id() == "iati"

    def test_read_activities(self):
        path = FIXTURES / "sample.iati.xml"
        with IATIIterable(filename=str(path)) as src:
            rows = list(src)
        assert len(rows) == 2
        assert rows[0]["iati-identifier"] == "AA-AAA-123456789-ABC123"
        assert rows[0]["title"] == "Sample Education Project"
        assert rows[1]["title"] == "Health Clinic Support"

    def test_write_not_supported(self):
        path = FIXTURES / "sample.iati.xml"
        with IATIIterable(filename=str(path)) as src:
            with pytest.raises(WriteNotSupportedError):
                src.write({"iati-identifier": "x"})


class TestIATIMissing:
    def test_import_error_when_missing(self):
        if HAS_LXML:
            pytest.skip("lxml is installed")
        with pytest.raises(ImportError, match="iterabledata\\[xml\\]"):
            IATIIterable(filename="x.xml")
