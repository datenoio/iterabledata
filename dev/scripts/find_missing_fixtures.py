#!/usr/bin/env python3
"""Report missing test fixture combinations (text+codec and binary golden files)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tests.conformance_fixtures import (  # noqa: E402
    discover_golden_fixtures,
    missing_golden_formats,
)

# Text-based data types that can be compressed
TEXT_DATATYPES = ["csv", "json", "jsonl", "ndjson", "xml"]

CODECS = {
    "br": "Brotli",
    "bz2": "BZip2",
    "gz": "GZip",
    "lz4": "LZ4",
    "xz": "LZMA",
    "zip": "ZIP",
    "zst": "ZStandard",
    "zstd": "ZStandard",
}

FIXTURES_DIR = ROOT / "tests" / "fixtures"


def _existing_files() -> set[str]:
    if not FIXTURES_DIR.is_dir():
        return set()
    return {p.name for p in FIXTURES_DIR.iterdir() if p.is_file()}


def _text_codec_report(existing: set[str]) -> int:
    expected: set[str] = set()
    for datatype in TEXT_DATATYPES:
        for codec_ext in CODECS:
            if codec_ext == "zstd":
                continue
            expected.add(f"2cols6rows.{datatype}.{codec_ext}")
            if datatype == "json":
                expected.add(f"2cols6rows_array.{datatype}.{codec_ext}")
                expected.add(f"2cols6rows_tag.{datatype}.{codec_ext}")
            if datatype == "jsonl":
                expected.add(f"2cols6rows_flat.{datatype}.{codec_ext}")
                expected.add(f"2cols6rows_flat.ndjson.{codec_ext}")
            if datatype == "xml":
                expected.add(f"books.{datatype}.{codec_ext}")

    missing = sorted(expected - existing)
    print("=" * 80)
    print("TEXT + CODEC FIXTURE COMBINATIONS")
    print("=" * 80)
    print(f"Expected: {len(expected)}  Present: {len(expected) - len(missing)}  Missing: {len(missing)}")
    if missing:
        print("\nMissing:")
        for name in missing:
            print(f"  - {name}")
    print()
    return len(missing)


def _binary_golden_report() -> int:
    fixtures = discover_golden_fixtures(FIXTURES_DIR)
    missing = missing_golden_formats(FIXTURES_DIR)
    print("=" * 80)
    print("BINARY / GOLDEN READ FIXTURES (2cols6rows.{format})")
    print("=" * 80)
    print(f"Formats with golden fixture: {len(fixtures)}")
    print(f"Formats missing golden fixture: {len(missing)}")
    if missing:
        print("\nMissing (primary registry keys):")
        for key in missing:
            print(f"  - {key}  (expected: 2cols6rows.{key} or override in conformance_fixtures.py)")
    print()
    return len(missing)


def main() -> int:
    existing = _existing_files()
    text_missing = _text_codec_report(existing)
    binary_missing = _binary_golden_report()
    total = text_missing + binary_missing
    print("=" * 80)
    print(f"SUMMARY: {total} total gaps ({text_missing} text+codec, {binary_missing} golden read)")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
