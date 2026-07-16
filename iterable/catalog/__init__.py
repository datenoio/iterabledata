"""Machine-readable format catalog for agents and tooling."""

from __future__ import annotations

import json
from typing import Any, Literal

from ..helpers.capabilities import get_format_capabilities
from ..helpers.format_registry import get_descriptor, iter_descriptors

__all__ = ["CATALOG_SCHEMA_VERSION", "describe_format", "export_catalog", "list_formats"]

CATALOG_SCHEMA_VERSION = "1.1"


def list_formats() -> list[str]:
    """Return sorted canonical format ids."""
    return sorted(desc.id for desc in iter_descriptors())


def describe_format(format_id: str, *, include_capabilities: bool = True) -> dict[str, Any]:
    """
    Describe a format by canonical id or alias.

    Merges declarative registry metadata with runtime capabilities when requested.
    """
    desc = get_descriptor(format_id.lower())
    if desc is None:
        raise ValueError(f"Unknown format: {format_id!r}")

    result: dict[str, Any] = {
        "id": desc.id,
        "aliases": list(desc.aliases),
        "module": desc.module,
        "class": desc.cls,
        "text": desc.text,
        "flat": desc.flat,
        "writable": desc.writable,
        "extra": desc.extra,
        "description": desc.description,
        "example_args": desc.example_args,
        "limitations": list(desc.limitations),
        "doc_url": desc.doc_url,
        "maturity": desc.maturity,
        "read_memory": desc.read_memory,
        "write_memory": desc.write_memory,
        "native_bulk_read": desc.native_bulk_read,
        "native_bulk_write": desc.native_bulk_write,
        "selection": list(desc.selection),
        "codec_support": list(desc.codec_support),
        "source_constraints": list(desc.source_constraints),
    }

    if include_capabilities:
        try:
            result["capabilities"] = get_format_capabilities(desc.id)
        except (ImportError, ValueError):
            result["capabilities"] = {}

    return result


def export_catalog(
    *,
    format: Literal["dict", "json"] = "dict",
    include_capabilities: bool = True,
) -> dict[str, Any] | str:
    """Export the full format catalog as a dict or JSON string."""
    catalog = {
        "_schema_version": CATALOG_SCHEMA_VERSION,
        **{fmt_id: describe_format(fmt_id, include_capabilities=include_capabilities) for fmt_id in list_formats()},
    }
    if format == "json":
        return json.dumps(catalog, indent=2, sort_keys=True)
    return catalog
