"""Downstream contract: every iterabledata name that undatum imports must keep existing.

undatum (https://github.com/datenoio/undatum) is the main consumer of this package. The list
below comes from ``git grep "from iterable" -- '*.py'`` in undatum plus the attributes it reads
from imported modules and the string paths its tests patch. Renaming or removing one of these
names breaks undatum; if a test here fails, keep a compatibility alias or coordinate the change
with undatum first.
"""

import importlib
import inspect
import shutil
from unittest import mock

import pytest

from iterable.convert import bulk_convert, convert

UNDATUM_IMPORTS = {
    "iterable.helpers.detect": [
        "detect_file_type",
        "open_iterable",
        "is_flat",
        "list_codecs",
        "CODEC_REGISTRY",
        "DATATYPE_REGISTRY",
        "TEXT_DATA_TYPES",
    ],
    "iterable.helpers.open_iterable": ["_get_codec_registry"],
    "iterable.helpers.capabilities": ["supports_write", "get_format_capabilities"],
    "iterable.helpers.utils": ["make_flat", "dict_generator", "detect_encoding_raw"],
    "iterable.helpers.typed": ["as_pydantic", "as_dataclasses"],
    "iterable.helpers.nested": ["project_row_nested"],
    "iterable.catalog": ["describe_format", "list_formats", "export_catalog"],
    "iterable.convert": ["convert", "bulk_convert"],
    "iterable.codecs.profiles": ["PROFILE_LEVELS"],
    "iterable.datatypes.csv": ["CSVIterable"],
    "iterable.dataframe_adapters": ["iterable_to_polars", "iterable_to_pandas", "iterable_to_dask"],
    "iterable.ops": ["schema"],
    "iterable.ops.schema": ["infer", "validate"],
    "iterable.ops.transform": ["apply_spec"],
    "iterable.types": ["ConversionResult"],
    "iterable.tools": [
        "analyze_dataset",
        "compute_stats",
        "convert_file",
        "describe_capabilities",
        "detect_format",
        "generate_documentation",
        "infer_schema",
        "plan_conversion",
        "read_sample",
        "suggest_transform",
        "tool_error",
        "tool_success",
        "schemas",
    ],
    "iterable.tools.schemas": ["TOOL_DEFINITIONS", "TOOL_HANDLERS", "call_tool"],
    "iterable.ai": ["blocks", "doc", "filter", "plan", "suggest"],
    "iterable.ai.blocks": [
        "BlockContext",
        "render_general_md",
        "render_schema_md",
        "_render_general_md",
        "_render_schema_md",
    ],
    "iterable.ai.doc": [
        "generate",
        "generate_blocks",
        "assemble_markdown",
        "ordered_block_keys",
        "_assemble_markdown",
        "_ordered_block_keys",
    ],
    "iterable.ai.semantic": [
        "mask_pii_samples",
        "run_metacrafter_scan",
        "parse_metacrafter_matches",
        "_run_metacrafter_scan",
        "_parse_metacrafter_matches",
    ],
    "iterable.ai.providers": ["get_provider"],
    "iterable.ai.metadata": [
        "classify_data_theme",
        "detect_languages",
        "extract_geographic_coverage",
        "extract_keywords",
        "extract_temporal_coverage",
    ],
    "iterable.ai.fileinfo": ["list_tables"],
    "iterable.ai.context": ["redact_for_llm"],
    "iterable.ai.filter": ["apply_ast", "translate_filter"],
    "iterable.ai.plan": ["plan_conversion"],
    "iterable.ai.suggest": ["suggest_transform"],
}

# Keyword arguments undatum passes to convert() and bulk_convert().
UNDATUM_CONVERT_KWARGS = {
    "iterableargs",
    "toiterableargs",
    "codecargs",
    "tocodecargs",
    "batch_size",
    "is_flatten",
    "use_native_batch",
    "selection",
    "strict_native",
    "atomic",
    "silent",
}


def _import(module_name):
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        # A missing optional third-party dependency is not a contract break; a missing
        # ``iterable.*`` module is.
        if e.name and not e.name.startswith("iterable"):
            pytest.skip(f"{module_name} needs optional dependency {e.name}")
        raise


@pytest.mark.parametrize(
    ("module_name", "name"),
    [(module, name) for module, names in UNDATUM_IMPORTS.items() for name in names],
)
def test_name_is_importable(module_name, name):
    module = _import(module_name)
    if not hasattr(module, name):
        # ``from package import submodule`` also resolves submodules that are not attributes yet.
        _import(f"{module_name}.{name}")
    assert hasattr(module, name), f"{module_name}.{name} is used by undatum"


@pytest.mark.parametrize(
    ("private", "public"),
    [
        ("iterable.ai.doc._assemble_markdown", "iterable.ai.doc.assemble_markdown"),
        ("iterable.ai.doc._ordered_block_keys", "iterable.ai.doc.ordered_block_keys"),
        ("iterable.ai.blocks._render_general_md", "iterable.ai.blocks.render_general_md"),
        ("iterable.ai.blocks._render_schema_md", "iterable.ai.blocks.render_schema_md"),
        ("iterable.ai.semantic._run_metacrafter_scan", "iterable.ai.semantic.run_metacrafter_scan"),
        ("iterable.ai.semantic._parse_metacrafter_matches", "iterable.ai.semantic.parse_metacrafter_matches"),
    ],
)
def test_private_names_alias_public_helpers(private, public):
    private_module, _, private_name = private.rpartition(".")
    public_module, _, public_name = public.rpartition(".")
    assert getattr(_import(private_module), private_name) is getattr(_import(public_module), public_name)


@pytest.mark.parametrize("function", [convert, bulk_convert])
def test_convert_accepts_undatum_kwargs(function):
    assert UNDATUM_CONVERT_KWARGS <= set(inspect.signature(function).parameters)


def test_list_codecs_matches_codec_registry():
    from iterable.helpers.detect import CODEC_REGISTRY, list_codecs
    from iterable.helpers.open_iterable import _get_codec_registry

    codecs = {c["id"]: c for c in list_codecs()}
    assert set(codecs) == set(_get_codec_registry())
    assert set(CODEC_REGISTRY) <= set(codecs)
    assert codecs["gz"] == {
        "id": "gz",
        "module": "iterable.codecs.gzipcodec",
        "class_name": "GZIPCodec",
        "source": "builtin",
    }
    assert {"bz2", "xz", "zip", "zst", "zstd"} <= set(codecs)


def test_registries_keep_their_shape():
    from iterable.helpers.detect import DATATYPE_REGISTRY, TEXT_DATA_TYPES

    module_path, class_name = DATATYPE_REGISTRY["csv"]
    assert (module_path, class_name) == ("iterable.datatypes.csv", "CSVIterable")
    assert "csv" in TEXT_DATA_TYPES
    assert "jsonl" in TEXT_DATA_TYPES


def test_patch_targets_used_by_undatum_tests():
    import iterable.convert

    with mock.patch("iterable.convert.convert") as patched:
        assert iterable.convert.convert is patched
    _import("iterable.ai.doc")
    with mock.patch("iterable.ai.providers.get_provider") as patched:
        assert importlib.import_module("iterable.ai.providers").get_provider is patched


def test_document_assembly_helpers():
    blocks = _import("iterable.ai.blocks")
    doc = _import("iterable.ai.doc")

    result_blocks = {
        "schema": {"markdown": blocks.render_schema_md([{"name": "id", "type": "integer", "nullable": False}])},
        "general": {"markdown": blocks.render_general_md({"title": "Sales", "record_count": 3}), "data": {}},
    }
    keys = doc.ordered_block_keys(result_blocks, ["general", "schema"])
    markdown = doc.assemble_markdown(blocks.BlockContext(language="English"), result_blocks, keys, None)

    assert keys == ["general", "schema"]
    assert markdown.startswith("# ")
    assert "**Sales**" in markdown
    assert "| id | integer |" in markdown
    assert markdown.index("**Sales**") < markdown.index("| id | integer |")


def test_metacrafter_helpers():
    semantic = _import("iterable.ai.semantic")

    matches = semantic.parse_metacrafter_matches({"matches": "email 0.95, phone", "datatype_url": "u"})
    assert matches == [
        {"type": "email", "url": "u", "confidence": 0.95},
        {"type": "phone", "url": "u", "confidence": None},
    ]
    with mock.patch.object(shutil, "which", return_value=None):
        assert semantic.run_metacrafter_scan("data.csv") is None
