"""Tests for the declarative format metadata registry."""

from pathlib import Path

import pytest

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    tomllib = pytest.importorskip("tomli")

from iterable.helpers.detect import (
    DATATYPE_REGISTRY,
    FLAT_TYPES,
    READ_ONLY_FORMATS,
    TEXT_DATA_TYPES,
)
from iterable.helpers.format_registry import (
    _CODEC_INSTALL_EXTRAS,
    _EXTRA_READ_ONLY,
    FORMAT_DESCRIPTORS,
    _basename_install_extras,
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
        """Every id in the derived read-only set traces to a writable=False descriptor."""
        for fmt_id in build_read_only_formats():
            if fmt_id in _EXTRA_READ_ONLY:
                continue
            desc = get_descriptor(fmt_id)
            assert desc is not None, fmt_id
            assert desc.writable is False, fmt_id

    def test_readonly_set_covers_all_nonwritable_descriptors(self):
        """Derived read-only set contains every non-writable descriptor id and alias."""
        read_only = build_read_only_formats()
        for desc in iter_descriptors():
            if desc.writable:
                continue
            assert desc.id in read_only, desc.id
            for alias in desc.aliases:
                assert alias in read_only, alias

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

    def test_all_formats_have_descriptions(self):
        for desc in iter_descriptors():
            assert desc.description, f"Missing description for {desc.id!r}"

    def test_llm_example_args_on_xml(self):
        xml = get_descriptor("xml")
        assert xml is not None
        assert xml.example_args == {"tagname": "item"}

    def test_iter_descriptors_yields_canonical_only(self):
        ids = {desc.id for desc in iter_descriptors()}
        assert "csv" in ids
        assert "tsv" not in ids
        assert len(ids) == len(FORMAT_DESCRIPTORS)

    def test_registry_classes_exported_in_datatypes(self):
        import importlib

        import iterable.datatypes as dt

        for desc in iter_descriptors():
            # The class name must always be advertised in __all__, regardless of
            # whether its optional dependency is installed.
            assert desc.cls in dt.__all__, desc.id

            # The class attribute is only present when the module imports
            # successfully; skip the attribute check when the optional
            # dependency is missing (ImportError swallowed in datatypes/__init__).
            try:
                importlib.import_module(desc.module)
            except ImportError:
                continue
            assert hasattr(dt, desc.cls), desc.id


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

    def test_llm_metadata_readonly_matches_writable_flag(self):
        """No format may be described as Read-only while its descriptor says writable."""
        from iterable.helpers.format_registry import _LLM_METADATA

        offenders = []
        for format_id, meta in _LLM_METADATA.items():
            desc = get_descriptor(format_id)
            if desc is None or not desc.writable:
                continue
            limitations = meta.get("limitations", ())
            if any("read-only" in str(item).lower() for item in limitations):
                offenders.append(format_id)
        assert not offenders, f"Writable formats with Read-only LLM metadata: {offenders}"

    def test_all_hints_map_to_pyproject_extras(self):
        pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
        extras = set(tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["optional-dependencies"])
        hints: set[str] = set()
        hints.update(_CODEC_INSTALL_EXTRAS.values())
        hints.update(_basename_install_extras().values())
        for desc in iter_descriptors():
            if desc.extra:
                hints.add(desc.extra)
            hint = install_extra_hint(desc.module)
            if hint:
                hints.add(hint)
        missing = sorted(h for h in hints if h not in extras)
        assert not missing, f"Install hints not in pyproject.toml extras: {missing}"


class TestDescriptorConformance:
    """Declared descriptor metadata must match importable implementations."""

    @staticmethod
    def _load_class(desc):
        import importlib

        module = importlib.import_module(desc.module)
        return getattr(module, desc.cls)

    def test_aliases_unique_and_collision_free(self):
        canonical_ids = {desc.id for desc in FORMAT_DESCRIPTORS}
        seen: dict[str, str] = {}
        for desc in FORMAT_DESCRIPTORS:
            for alias in desc.aliases:
                assert alias not in canonical_ids, f"alias {alias!r} collides with a canonical id"
                assert alias not in seen, f"alias {alias!r} claimed by both {seen[alias]!r} and {desc.id!r}"
                seen[alias] = desc.id

    def test_alias_magic_targets_own_alias(self):
        for desc in FORMAT_DESCRIPTORS:
            for alias, _prefix in desc.alias_magic:
                assert alias in desc.aliases, f"{desc.id}: alias_magic targets non-alias {alias!r}"

    def test_magic_signatures_trace_to_descriptors(self):
        from iterable.helpers.format_registry import MAGIC_SIGNATURES

        expected = set()
        for desc in FORMAT_DESCRIPTORS:
            for prefix in desc.magic:
                expected.add((desc.id, prefix))
            for alias, prefix in desc.alias_magic:
                expected.add((alias, prefix))
        actual = {(sig.format_id, sig.prefix) for sig in MAGIC_SIGNATURES}
        assert actual == expected
        for sig in MAGIC_SIGNATURES:
            assert sig.format_id in DATATYPE_REGISTRY, sig.format_id

    def test_vortex_magic_reports_alias(self):
        assert match_magic_prefix(b"VTXF" + b"\x00" * 10) == ("vortex", 0.99, "magic_number")

    def test_pcapng_magic_reports_alias(self):
        assert match_magic_prefix(b"\x0a\x0d\x0d\x0a" + b"\x00" * 10) == ("pcapng", 0.99, "magic_number")

    def test_orc_and_arrow_magic(self):
        assert match_magic_prefix(b"ORC" + b"\x00" * 10) == ("orc", 0.99, "magic_number")
        assert match_magic_prefix(b"ARROW1" + b"\x00" * 10) == ("arrow", 0.99, "magic_number")

    def test_writable_declarations_have_real_writers(self):
        """writable=True must not resolve to the base unsupported writer."""
        import inspect

        import pytest

        from iterable.base import BaseIterable
        from iterable.helpers.capabilities import get_format_capabilities

        for desc in iter_descriptors():
            if not desc.writable:
                continue
            try:
                cls = self._load_class(desc)
            except ImportError:
                pytest.skip(f"optional dependency missing for {desc.id}")
            assert cls.write is not BaseIterable.write, f"{desc.id}: writable=True but uses base writer"
            try:
                source = inspect.getsource(cls.write)
            except (OSError, TypeError):
                continue
            if "WriteNotSupportedError" in source:
                lines = [
                    ln.strip()
                    for ln in source.split("\n")
                    if ln.strip()
                    and not ln.strip().startswith("#")
                    and not ln.strip().startswith('"""')
                    and not ln.strip().startswith("'''")
                ]
                assert len(lines) > 3, f"{desc.id}: writable=True but write() only raises WriteNotSupportedError"
            assert get_format_capabilities(desc.id)["writable"] is True

    def test_native_bulk_declarations_have_owned_implementations(self):
        """Native bulk requires a format-specific bulk path, not the base loop.

        A declaration is satisfied by an owned read_bulk()/write_bulk() below
        the base classes or by a backend batch path in the class source
        (e.g. ``to_batches``/scan/fetchmany iteration behind read()).
        """
        import inspect

        import pytest

        batch_markers = ("to_batches", ".scan(", "fetchmany", "RecordBatch", "batch_size")

        for desc in iter_descriptors():
            if not desc.native_bulk_read and not desc.native_bulk_write:
                continue
            try:
                cls = self._load_class(desc)
            except ImportError:
                pytest.skip(f"optional dependency missing for {desc.id}")

            def owner(name, cls=cls):  # noqa: B023 - intentional late binding per format
                for klass in cls.__mro__:
                    if name in klass.__dict__:
                        return klass.__name__
                return None

            try:
                source = inspect.getsource(cls)
            except (OSError, TypeError):
                source = ""
            has_backend_batch = any(marker in source for marker in batch_markers)

            if desc.native_bulk_read:
                owned = owner("read_bulk") not in (None, "BaseIterable", "BaseFileIterable")
                assert owned or has_backend_batch, (
                    f"{desc.id}: native_bulk_read=True but only the inherited base loop exists"
                )
            if desc.native_bulk_write:
                owned = owner("write_bulk") not in (None, "BaseIterable", "BaseFileIterable")
                assert owned or has_backend_batch, (
                    f"{desc.id}: native_bulk_write=True but only the inherited base loop exists"
                )

    def test_totals_tables_match_implementation(self):
        """Descriptor totals/tables declarations match has_totals()/has_tables()."""
        import pytest

        from iterable.helpers.capabilities import get_format_capabilities

        for desc in iter_descriptors():
            try:
                cls = self._load_class(desc)
            except ImportError:
                pytest.skip(f"optional dependency missing for {desc.id}")
            assert desc.totals == cls.has_totals(), f"{desc.id}: totals declaration contradicts has_totals()"
            assert desc.tables == cls.has_tables(), f"{desc.id}: tables declaration contradicts has_tables()"
            caps = get_format_capabilities(desc.id)
            assert caps["totals"] == desc.totals, desc.id
            assert caps["tables"] == desc.tables, desc.id

    def test_capability_dict_matches_descriptor(self):
        """The capability layer reports descriptor values for every built-in."""
        from iterable.helpers.capabilities import get_format_capabilities

        for desc in iter_descriptors():
            caps = get_format_capabilities(desc.id)
            assert caps["writable"] == desc.writable, desc.id
            assert caps["flat_only"] == desc.flat, desc.id
            assert caps["nested"] == (not desc.flat), desc.id
            assert caps["native_bulk_read"] == desc.native_bulk_read, desc.id
            assert caps["native_bulk_write"] == desc.native_bulk_write, desc.id
            assert caps["read_memory"] == desc.read_memory, desc.id
            assert caps["write_memory"] == desc.write_memory, desc.id
            assert caps["selection"] == list(desc.selection), desc.id
            assert caps["codec_support"] == list(desc.codec_support), desc.id
            assert caps["source_constraints"] == list(desc.source_constraints), desc.id
            assert caps["maturity"] == desc.maturity, desc.id
            # Aliases report the same values as the canonical id
            for alias in desc.aliases:
                assert get_format_capabilities(alias) == caps, f"{desc.id} vs alias {alias}"
