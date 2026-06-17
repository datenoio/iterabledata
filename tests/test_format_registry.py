"""Tests for the declarative format metadata registry."""

from iterable.helpers.detect import (
    DATATYPE_REGISTRY,
    FLAT_TYPES,
    READ_ONLY_FORMATS,
    TEXT_DATA_TYPES,
)
from iterable.helpers.format_registry import (
    _EXTRA_READ_ONLY,
    _READONLY_MEMBERS,
    _TEXT_ORPHANS,
    FORMAT_DESCRIPTORS,
    build_datatype_registry,
    build_flat_types,
    build_read_only_formats,
    build_text_data_types,
    get_descriptor,
    install_extra_hint,
    iter_descriptors,
    match_magic_prefix,
)


class TestDerivedStructures:
    def test_datatype_registry_matches_legacy(self):
        assert build_datatype_registry() == DATATYPE_REGISTRY

    def test_read_only_formats_matches_legacy(self):
        assert build_read_only_formats() == READ_ONLY_FORMATS

    def test_text_data_types_matches_legacy(self):
        assert build_text_data_types() == TEXT_DATA_TYPES

    def test_flat_types_matches_legacy(self):
        assert build_flat_types() == FLAT_TYPES


class TestDescriptorConsistency:
    def test_each_descriptor_has_unique_canonical_id(self):
        ids = [desc.id for desc in FORMAT_DESCRIPTORS]
        assert len(ids) == len(set(ids))

    def test_registry_keys_resolve_to_descriptors(self):
        for key in DATATYPE_REGISTRY:
            assert get_descriptor(key) is not None

    def test_readonly_members_have_writable_false(self):
        for fmt_id in _READONLY_MEMBERS:
            if fmt_id in _TEXT_ORPHANS:
                continue
            desc = get_descriptor(fmt_id)
            assert desc is not None, fmt_id
            assert desc.writable is False, fmt_id

    def test_readonly_orphans_allowed(self):
        assert "zipped" in _EXTRA_READ_ONLY
        assert "zipped" in READ_ONLY_FORMATS
        assert "zipped" not in DATATYPE_REGISTRY


class TestLookupAPI:
    def test_get_descriptor_by_id_and_alias(self):
        csv = get_descriptor("csv")
        tsv = get_descriptor("tsv")
        assert csv is not None
        assert tsv is csv

    def test_get_descriptor_unknown(self):
        assert get_descriptor("not-a-format") is None

    def test_llm_metadata_on_csv(self):
        csv = get_descriptor("csv")
        assert csv is not None
        assert csv.description is not None
        assert csv.doc_url is not None

    def test_llm_example_args_on_xml(self):
        xml = get_descriptor("xml")
        assert xml is not None
        assert xml.example_args == {"tagname": "item"}

    def test_iter_descriptors_yields_canonical_only(self):
        ids = {desc.id for desc in iter_descriptors()}
        assert "csv" in ids
        assert "tsv" not in ids
        assert len(ids) == len(FORMAT_DESCRIPTORS)


class TestMagicPrefixMatching:
    def test_parquet_magic(self):
        result = match_magic_prefix(b"PAR1" + b"\x00" * 10)
        assert result == ("parquet", 0.99, "magic_number")

    def test_pcap_magic(self):
        result = match_magic_prefix(b"\xa1\xb2\xc3\xd4" + b"\x00" * 10)
        assert result == ("pcap", 0.99, "magic_number")

    def test_xlsx_magic(self):
        peek = b"PK\x03\x04" + b"\x00" * 20 + b"xl/worksheets" + b"\x00" * 50
        result = match_magic_prefix(peek)
        assert result == ("xlsx", 0.95, "magic_number")

    def test_generic_zip_magic(self):
        peek = b"PK\x03\x04" + b"\x00" * 100
        result = match_magic_prefix(peek)
        assert result == ("zip", 0.90, "magic_number")


class TestCapabilitiesIntegration:
    def test_is_read_only_uses_descriptor(self):
        from iterable.helpers.capabilities import _is_read_only

        assert _is_read_only("pcap") is True
        assert _is_read_only("csv") is False
        assert _is_read_only("zipped") is True  # orphan id, not in DATATYPE_REGISTRY


class TestInstallHints:
    def test_install_extra_hint_known_module(self):
        assert install_extra_hint("iterable.datatypes.parquet") == "parquet"
        assert install_extra_hint("iterable.datatypes.bsonf") == "bson"

    def test_install_extra_hint_unknown_module(self):
        assert install_extra_hint("iterable.datatypes.csv") is None
