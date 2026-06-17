"""Tests for iterable.catalog module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from iterable.catalog import describe_format, export_catalog, list_formats


class TestListFormats:
    def test_list_formats_sorted(self):
        formats = list_formats()
        assert formats == sorted(formats)
        assert "csv" in formats
        assert "parquet" in formats
        assert len(formats) >= 100


class TestDescribeFormat:
    def test_describe_by_id(self):
        info = describe_format("csv", include_capabilities=False)
        assert info["id"] == "csv"
        assert info["text"] is True
        assert info["flat"] is True
        assert info["description"] is not None
        assert "csv.md" in (info["doc_url"] or "")

    def test_describe_by_alias(self):
        info = describe_format("tsv", include_capabilities=False)
        assert info["id"] == "csv"
        assert "tsv" in info["aliases"]

    def test_describe_xml_example_args(self):
        info = describe_format("xml", include_capabilities=False)
        assert info["example_args"] == {"tagname": "item"}

    def test_describe_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown format"):
            describe_format("not-a-real-format")


class TestExportCatalog:
    def test_export_dict(self):
        catalog = export_catalog(format="dict", include_capabilities=False)
        assert isinstance(catalog, dict)
        assert "jsonl" in catalog
        assert catalog["jsonl"]["text"] is True

    def test_export_json_roundtrip(self):
        raw = export_catalog(format="json", include_capabilities=False)
        assert isinstance(raw, str)
        parsed = json.loads(raw)
        assert "parquet" in parsed


class TestFormatsJsonArtifact:
    def test_formats_json_matches_export(self):
        path = Path(__file__).resolve().parents[1] / "dev" / "formats.json"
        assert path.is_file(), "Run dev/scripts/export_formats_json.py to create dev/formats.json"
        committed = json.loads(path.read_text(encoding="utf-8"))
        live = export_catalog(format="dict", include_capabilities=True)
        assert set(committed.keys()) == set(live.keys())
        for fmt_id in ("csv", "xml", "parquet"):
            assert committed[fmt_id]["id"] == live[fmt_id]["id"]
            assert committed[fmt_id]["description"] == live[fmt_id]["description"]
