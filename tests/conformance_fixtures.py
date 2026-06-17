"""Golden fixture discovery for registry-driven conformance tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from iterable.helpers.detect import DATATYPE_REGISTRY
from iterable.helpers.format_registry import get_descriptor

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Relative paths under tests/ (conftest chdirs to tests/)
GoldenFixture = tuple[str, dict[str, Any] | None]

GOLDEN_PREFIX = "2cols6rows"

# Fixtures that do not follow ``2cols6rows.{ext}`` naming.
FIXTURE_OVERRIDES: dict[str, GoldenFixture] = {
    "jsonl": ("fixtures/2cols6rows_flat.jsonl", None),
    "ndjson": ("fixtures/2cols6rows_flat.ndjson", None),
    "json": ("fixtures/2cols6rows_array.json", None),
    "jsonld": ("fixtures/2cols6rows_array.jsonld", None),
    "yaml": ("fixtures/2cols6rows_flat.yaml", None),
    "yml": ("fixtures/2cols6rows_flat.yaml", None),
    "msgpack": ("fixtures/2cols6rows_flat.msgpack", None),
    "mp": ("fixtures/2cols6rows_flat.msgpack", None),
    "bson": ("fixtures/2cols6rows_flat.bson", None),
    "pickle": ("fixtures/2cols6rows_flat.pickle", None),
    "vortex": ("fixtures/2cols6rows.vortex", None),
    "vtx": ("fixtures/2cols6rows.vortex", None),
    "xml": ("fixtures/books.xml", {"tagname": "book"}),
    "fwf": ("fixtures/2cols6rows.fwf", {"widths": [3, 10], "names": ["id", "name"]}),
}


def _registry_keys_for_format(format_key: str) -> set[str]:
    desc = get_descriptor(format_key)
    keys = {format_key}
    if desc is not None:
        keys.add(desc.id)
        keys.update(desc.aliases)
    return keys


def discover_golden_fixtures(fixtures_dir: Path | None = None) -> dict[str, GoldenFixture]:
    """Map registry extension keys to golden read fixtures.

    Scans ``2cols6rows.{ext}`` files (single extension, no compression suffix) and
    merges explicit overrides for variant layouts (flat JSONL, books.xml, etc.).
    """
    root = fixtures_dir or FIXTURES_DIR
    discovered: dict[str, GoldenFixture] = {}

    for path in sorted(root.glob(f"{GOLDEN_PREFIX}.*")):
        if path.name.count(".") != 1:
            continue
        ext = path.name.split(".", 1)[1]
        if ext in DATATYPE_REGISTRY:
            discovered[ext] = (f"fixtures/{path.name}", None)

    for key, spec in FIXTURE_OVERRIDES.items():
        rel_path, args = spec
        if (root / rel_path.removeprefix("fixtures/")).exists():
            discovered[key] = (rel_path, dict(args) if args else None)

    return discovered


def canonical_fixture_formats(fixtures: dict[str, GoldenFixture] | None = None) -> dict[str, GoldenFixture]:
    """One fixture entry per unique format class (prefer primary registry key)."""
    fixtures = fixtures or discover_golden_fixtures()
    by_class: dict[tuple[str, str], str] = {}
    for key in DATATYPE_REGISTRY:
        by_class.setdefault(DATATYPE_REGISTRY[key], key)

    canonical: dict[str, GoldenFixture] = {}
    for _target, primary_key in by_class.items():
        keys = _registry_keys_for_format(primary_key)
        for candidate in (primary_key, *sorted(keys)):
            if candidate in fixtures:
                canonical[primary_key] = fixtures[candidate]
                break
    return canonical


def missing_golden_formats(fixtures_dir: Path | None = None) -> list[str]:
    """Registry primary keys with no golden read fixture."""
    fixtures = discover_golden_fixtures(fixtures_dir)
    canonical = canonical_fixture_formats(fixtures)
    by_class: dict[tuple[str, str], str] = {}
    for key in DATATYPE_REGISTRY:
        by_class.setdefault(DATATYPE_REGISTRY[key], key)
    return sorted(k for k in by_class.values() if k not in canonical)
