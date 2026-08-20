#!/usr/bin/env python3
"""Generate Docusaurus format doc stubs for formats missing a docs page."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORMATS_DIR = ROOT / "docs" / "docs" / "formats"
TEMPLATE = ROOT / "docs" / "FORMAT_PAGE_TEMPLATE.md"


def _doc_path(format_id: str) -> Path:
    from iterable.helpers.format_descriptions import DOC_FILENAMES

    name = DOC_FILENAMES.get(format_id, f"{format_id}.md")
    return FORMATS_DIR / name


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from iterable.helpers.format_registry import iter_descriptors

    if not TEMPLATE.is_file():
        print(f"Template not found: {TEMPLATE}", file=sys.stderr)
        return 1

    template = TEMPLATE.read_text(encoding="utf-8")
    created = 0
    for desc in iter_descriptors():
        path = _doc_path(desc.id)
        if path.is_file():
            continue
        title = desc.id.upper()
        body = (
            template.replace("[Format Name]", title)
            .replace("[Brief description of the format]", desc.description or f"{title} data format.")
            .replace("[ext]", desc.id)
        )
        path.write_text(body, encoding="utf-8")
        print(f"Created stub: {path.relative_to(ROOT)}")
        created += 1

    print(f"Done. Created {created} stub(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
