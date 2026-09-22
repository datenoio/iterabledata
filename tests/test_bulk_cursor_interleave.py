"""Interleaved read()/read_bulk()/reset() conformance for custom bulk readers.

Every datatype that overrides ``BaseIterable.read_bulk()`` must consume records
through one logical cursor: single-row reads, bulk reads, and ``reset()`` must
never duplicate, drop, or reorder records.

Coverage is registry-driven and split into three tiers:

- Golden fixtures: formats with an auto-discovered ``2cols6rows`` fixture are
  read through ``open_iterable()`` (see tests/conformance_fixtures.py).
- Inline builders: formats without a golden fixture get a small tmp/stream
  fixture — either a round-trip through the format's own writer or a
  hand-crafted minimal input. Builders that depend on missing optional
  dependencies skip cleanly (``pytest.skip`` on ImportError /
  ``pytest.importorskip``).
- Documented skips: formats that cannot be exercised in this environment
  (missing native/geo dependency stacks and no committed fixture) carry an
  explicit reason in ``EXPLICIT_SKIPS``.

``test_all_custom_bulk_readers_have_coverage`` fails when a new custom bulk
reader lands in the registry without landing in one of the tiers.
"""

from __future__ import annotations

import io
import json
import os
from collections.abc import Callable
from pathlib import Path

import pytest
from conformance_fixtures import canonical_fixture_formats

from iterable.exceptions import IterableDataError
from iterable.helpers.detect import DATATYPE_REGISTRY, _load_symbol, open_iterable

FIXTURE_FORMATS = canonical_fixture_formats()
COMMITTED_FIXTURES = Path(__file__).parent / "fixtures"

# ---------------------------------------------------------------------------
# Registry introspection: which formats override read_bulk()?
# ---------------------------------------------------------------------------


def _unique_format_classes() -> dict[tuple[str, str], str]:
    """Map registry ``(module, symbol)`` targets to their primary key."""
    by_class: dict[tuple[str, str], str] = {}
    for key, target in DATATYPE_REGISTRY.items():
        by_class.setdefault(target, key)
    return by_class


def _has_custom_read_bulk(cls: type) -> bool:
    """True when the first MRO provider of read_bulk is not BaseIterable."""
    for klass in cls.__mro__:
        if "read_bulk" in klass.__dict__:
            return klass.__name__ != "BaseIterable"
    return False


def _classify_formats() -> tuple[dict[str, type | None], set[str]]:
    """Split registry primary keys into custom-bulk readers and base-bulk readers.

    Returns ``(custom, base_only)`` where ``custom`` maps the primary key to the
    loaded class (or ``None`` when an optional dependency blocks the import, in
    which case the source-level ``def read_bulk`` is assumed custom).
    """
    custom: dict[str, type | None] = {}
    base_only: set[str] = set()
    for target, primary in _unique_format_classes().items():
        try:
            cls = _load_symbol(*target)
        except ImportError:
            # Module-level optional dependency missing (e.g. dbfread). The class
            # cannot be introspected; golden/builder tiers still cover the key.
            custom[primary] = None
            continue
        if _has_custom_read_bulk(cls):
            custom[primary] = cls
        else:
            base_only.add(primary)
    return custom, base_only


CUSTOM_BULK, BASE_BULK_ONLY = _classify_formats()

# Golden-fixture tier: read via open_iterable like the main conformance suite.
GOLDEN_KEYS = sorted(k for k in CUSTOM_BULK if k in FIXTURE_FORMATS)

# ---------------------------------------------------------------------------
# Inline builders (formats without a golden fixture)
# ---------------------------------------------------------------------------

Opener = Callable[[], object]
Builder = Callable[[Path], Opener]

FLAT_ROWS = [{"id": index, "name": f"row-{index}"} for index in range(6)]
GENO_ROWS = [
    {"chrom": "chr1", "start": 100 + index * 50, "end": 150 + index * 50, "name": f"feature-{index}", "strand": "+"}
    for index in range(6)
]
BED_ROWS = [
    {"chrom": "chr1", "start": 100 + index * 50, "end": 150 + index * 50, "name": f"feature-{index}"}
    for index in range(6)
]
GRID_ROWS = [{"row": 0, "col": index, "value": float(index)} for index in range(6)]

ARFF_TEXT = """@RELATION interleave
@ATTRIBUTE id NUMERIC
@ATTRIBUTE name STRING
@DATA
1,row-0
2,row-1
3,row-2
4,row-3
5,row-4
6,row-5
"""

MIF_TEXT = """Version 300
Charset "WindowsLatin1"
Delimiter ","
CoordSys Earth Projection 1, 62
Columns 2
  id Integer
  name Char(20)
Data
Point 1 1
    Symbol (35,0,12)
Point 2 2
    Symbol (35,0,12)
Point 3 3
    Symbol (35,0,12)
Point 4 4
    Symbol (35,0,12)
Point 5 5
    Symbol (35,0,12)
Point 6 6
    Symbol (35,0,12)
"""

# GDAL's MapInfo driver reads attribute values from the companion .mid file.
MID_TEXT = """1,"row-0"
2,"row-1"
3,"row-2"
4,"row-3"
5,"row-4"
6,"row-5"
"""

OTLP_DOCUMENT = {
    "resourceSpans": [
        {
            "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "interleave"}}]},
            "scopeSpans": [
                {
                    "scope": {"name": "lib"},
                    "spans": [{"traceId": f"trace-{index}", "name": f"span-{index}"} for index in range(6)],
                }
            ],
        }
    ]
}


def _load(module: str, symbol: str) -> type:
    """Lazy datatype import so missing optional deps surface as skips at call time."""
    return _load_symbol(module, symbol)


def _roundtrip_builder(
    module: str,
    symbol: str,
    filename: str,
    rows: list[dict],
    open_kwargs: dict | None = None,
    write_kwargs: dict | None = None,
) -> Builder:
    """Build an opener that reads a tmp file written by the format's own writer."""

    def build(tmp_path: Path) -> Opener:
        cls = _load(module, symbol)
        path = tmp_path / filename
        with cls(str(path), mode="w", **(write_kwargs or {})) as output:
            for row in rows:
                output.write(dict(row))

        def opener() -> object:
            return cls(str(path), **(open_kwargs or {}))

        return opener

    return build


def _text_fixture_builder(module: str, symbol: str, filename: str, content: str) -> Builder:
    """Build an opener over a hand-crafted text fixture (read-only formats)."""

    def build(tmp_path: Path) -> Opener:
        path = tmp_path / filename
        path.write_text(content, encoding="utf-8")

        def opener() -> object:
            return _load(module, symbol)(str(path))

        return opener

    return build


def _mif_builder(tmp_path: Path) -> Opener:
    """Write a valid MapInfo .mif/.mid pair (geometry + attributes)."""
    mif_path = tmp_path / "rows.mif"
    mif_path.write_text(MIF_TEXT, encoding="utf-8")
    (tmp_path / "rows.mid").write_text(MID_TEXT, encoding="utf-8")

    def opener() -> object:
        return _load("iterable.datatypes.mif", "MapInfoIterable")(str(mif_path))

    return opener


def _e00_builder(tmp_path: Path) -> Opener:
    fixture = COMMITTED_FIXTURES / "sample.e00"
    if not fixture.exists():
        pytest.skip("Committed fixture tests/fixtures/sample.e00 not found")

    def opener() -> object:
        return _load("iterable.datatypes.e00", "E00Iterable")(str(fixture))

    return opener


def _otlp_json_builder(tmp_path: Path) -> Opener:
    payload = json.dumps(OTLP_DOCUMENT)

    def opener() -> object:
        cls = _load("iterable.datatypes.otlp", "OTLPJSONIterable")
        return cls.from_stream(io.StringIO(payload))

    return opener


def _cram_builder(tmp_path: Path) -> Opener:
    pysam = pytest.importorskip("pysam")
    reference = tmp_path / "reference.fa"
    reference.write_text(">chr1\n" + "ACGT" * 250 + "\n", encoding="utf-8")
    pysam.faidx(str(reference))
    header = {"HD": {"VN": "1.6", "SO": "coordinate"}, "SQ": [{"LN": 1000, "SN": "chr1"}]}
    cram_path = tmp_path / "rows.cram"
    with pysam.AlignmentFile(str(cram_path), "wc", header=header, reference_filename=str(reference)) as output:
        for index in range(6):
            segment = pysam.AlignedSegment()
            segment.query_name = f"read-{index}"
            segment.query_sequence = "ACGTACGTAC"
            segment.flag = 0
            segment.reference_id = 0
            segment.reference_start = index * 100
            segment.mapping_quality = 60
            segment.cigar = ((0, 10),)
            output.write(segment)

    def opener() -> object:
        cls = _load("iterable.datatypes.cram", "CRAMIterable")
        return cls(str(cram_path), reference_filename=str(reference))

    return opener


BUILDERS: dict[str, Builder] = {
    "psv": _roundtrip_builder("iterable.datatypes.psv", "PSVIterable", "rows.psv", FLAT_ROWS),
    "ssv": _roundtrip_builder("iterable.datatypes.psv", "SSVIterable", "rows.ssv", FLAT_ROWS),
    "db": _roundtrip_builder("iterable.datatypes.sqlite", "SQLiteIterable", "rows.db", FLAT_ROWS),
    "gelf": _roundtrip_builder("iterable.datatypes.gelf", "GELIterable", "rows.gelf", FLAT_ROWS),
    "gff3": _roundtrip_builder("iterable.datatypes.genomic_intervals", "GFF3Iterable", "rows.gff3", GENO_ROWS),
    "gtf": _roundtrip_builder("iterable.datatypes.genomic_intervals", "GTFIterable", "rows.gtf", GENO_ROWS),
    "czml": _roundtrip_builder("iterable.datatypes.czml", "CZMLIterable", "rows.czml", FLAT_ROWS),
    "bed": _roundtrip_builder("iterable.datatypes.bed", "BEDIterable", "rows.bed", BED_ROWS),
    "asc": _roundtrip_builder("iterable.datatypes.asciigrid", "ASCIIGridIterable", "rows.asc", GRID_ROWS),
    # Writers raise ImportError when the optional dependency is missing -> clean skip.
    "zarr": _roundtrip_builder("iterable.datatypes.zarr", "ZarrIterable", "rows.zarr", FLAT_ROWS),
    # Read-only formats with hand-crafted or generated fixtures.
    "arff": _text_fixture_builder("iterable.datatypes.arff", "ARFFIterable", "rows.arff", ARFF_TEXT),
    "mif": _mif_builder,
    "e00": _e00_builder,
    "cram": _cram_builder,
    "otlp-json": _otlp_json_builder,
}

# Formats that cannot be exercised in this environment: the optional native/geo
# dependency stack is absent, there is no committed fixture, and an inline
# fixture cannot be validated without the stack installed.
EXPLICIT_SKIPS: dict[str, str] = {
    "las": "LAS requires laspy and a binary LAS fixture; none committed and inline crafting is unvalidated here",
    "bag": "BAG requires h5py with a valid BAG HDF5 layout; no committed fixture",
    "fgdb": "File Geodatabase requires Fiona with a FileGDB driver (read-only); no committed fixture",
    "otlp-protobuf": "OTLP Protobuf requires protobuf; no committed fixture and no validated inline builder",
}


# ---------------------------------------------------------------------------
# Provider resolution
# ---------------------------------------------------------------------------


def _golden_opener(format_key: str) -> Opener:
    path, iterableargs = FIXTURE_FORMATS[format_key]
    if not os.path.exists(path):
        pytest.skip(f"Fixture {path} not found")

    def opener() -> object:
        return open_iterable(path, iterableargs=dict(iterableargs) if iterableargs else None)

    return opener


def _resolve_opener(format_key: str, tmp_path: Path) -> Opener:
    if format_key in GOLDEN_KEYS:
        return _golden_opener(format_key)
    if format_key in BUILDERS:
        try:
            return BUILDERS[format_key](tmp_path)
        except ImportError as e:
            pytest.skip(f"Optional dependency missing for {format_key!r}: {e}")
    reason = EXPLICIT_SKIPS.get(format_key)
    if reason is not None:
        pytest.skip(f"{format_key}: {reason}")
    pytest.fail(f"{format_key}: custom bulk reader has no interleave coverage (update GOLDEN/BUILDERS/EXPLICIT_SKIPS)")


def _open_or_skip(opener: Opener, format_key: str):
    try:
        return opener()
    except ImportError as e:
        pytest.skip(f"Optional dependency missing for {format_key!r}: {e}")
    except (RuntimeError, IterableDataError) as e:
        if isinstance(e.__cause__, ImportError) or "requires" in str(e):
            pytest.skip(f"Optional dependency missing for {format_key}: {e}")
        raise


# ---------------------------------------------------------------------------
# Interleave driver
# ---------------------------------------------------------------------------

# read two rows singly, then a small bulk, then one singly, then a larger bulk,
# one more single row, then a bulk larger than the remainder. Any correct shared
# cursor must deliver exactly the full sequence with no duplication or loss.
_PATTERN: tuple[tuple[str, int | None], ...] = (
    ("read", None),
    ("read", None),
    ("bulk", 2),
    ("read", None),
    ("bulk", 3),
    ("read", None),
    ("bulk", 100),
)

_MAX_ROWS = 10_000


def _read_all(source) -> list[dict]:
    rows: list[dict] = []
    while len(rows) < _MAX_ROWS:
        try:
            rows.append(source.read())
        except StopIteration:
            return rows
    raise AssertionError(f"source produced more than {_MAX_ROWS} rows; fixture should be small")


def _interleaved_rows(source) -> list[dict]:
    rows: list[dict] = []
    for op, num in _PATTERN:
        if op == "read":
            try:
                rows.append(source.read())
            except StopIteration:
                return rows
        else:
            assert num is not None
            chunk = source.read_bulk(num)
            assert isinstance(chunk, list), f"read_bulk({num}) returned {type(chunk).__name__}, expected list"
            assert len(chunk) <= num, f"read_bulk({num}) returned {len(chunk)} rows"
            rows.extend(chunk)
            if not chunk:
                return rows
    while len(rows) < _MAX_ROWS:
        try:
            rows.append(source.read())
        except StopIteration:
            return rows
    raise AssertionError(f"source produced more than {_MAX_ROWS} rows; fixture should be small")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

PARAM_KEYS = sorted(CUSTOM_BULK)


@pytest.mark.parametrize("format_key", PARAM_KEYS)
def test_interleaved_read_and_bulk_exact_sequence(format_key, tmp_path):
    """Interleaved read()/read_bulk() yields the exact full row sequence once."""
    opener = _resolve_opener(format_key, tmp_path)
    with _open_or_skip(opener, format_key) as source:
        expected = _read_all(source)
    assert expected, f"{format_key}: fixture produced no rows"
    with _open_or_skip(opener, format_key) as source:
        interleaved = _interleaved_rows(source)
    assert interleaved == expected, (
        f"{format_key}: interleaved read()/read_bulk() sequence differs from the row-by-row sequence "
        f"({len(interleaved)} rows vs {len(expected)})"
    )


@pytest.mark.parametrize("format_key", PARAM_KEYS)
def test_interleaved_reset_replays_exact_sequence(format_key, tmp_path):
    """After interleaved reads, reset() replays the identical interleaved sequence."""
    opener = _resolve_opener(format_key, tmp_path)
    with _open_or_skip(opener, format_key) as source:
        expected = _read_all(source)
    assert expected, f"{format_key}: fixture produced no rows"
    with _open_or_skip(opener, format_key) as source:
        first_pass = _interleaved_rows(source)
        assert first_pass == expected, f"{format_key}: first interleaved pass lost or duplicated rows"
        try:
            source.reset()
        except (NotImplementedError, ValueError) as e:
            pytest.skip(f"{format_key}: reset not supported: {e}")
        second_pass = _interleaved_rows(source)
    assert second_pass == expected, f"{format_key}: interleaved sequence after reset() differs from the first pass"


def test_all_custom_bulk_readers_have_coverage():
    """Every custom bulk reader must land in exactly one coverage tier."""
    provided = set(GOLDEN_KEYS) | set(BUILDERS) | set(EXPLICIT_SKIPS)
    missing = set(CUSTOM_BULK) - provided
    assert not missing, f"Custom bulk readers without interleave coverage: {sorted(missing)}"

    unknown = provided - set(DATATYPE_REGISTRY)
    assert not unknown, f"Coverage entries for unregistered formats: {sorted(unknown)}"

    stale = provided & BASE_BULK_ONLY
    assert not stale, f"Coverage entries for formats that no longer override read_bulk(): {sorted(stale)}"

    assert not (set(BUILDERS) & set(GOLDEN_KEYS)), (
        f"Formats with both a golden fixture and a builder (drop the builder): "
        f"{sorted(set(BUILDERS) & set(GOLDEN_KEYS))}"
    )
    overlaps = set(EXPLICIT_SKIPS) & (set(BUILDERS) | set(GOLDEN_KEYS))
    assert not overlaps, f"Formats with both a skip reason and real coverage: {sorted(overlaps)}"
    empty_reasons = [key for key, reason in EXPLICIT_SKIPS.items() if not reason.strip()]
    assert not empty_reasons, f"Explicit skips without a documented reason: {empty_reasons}"
