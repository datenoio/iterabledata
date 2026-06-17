#!/usr/bin/env python3
"""Export dev/formats.json from iterable.catalog."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "dev" / "formats.json"


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from iterable.catalog import export_catalog

    catalog_json = export_catalog(format="json", include_capabilities=True)
    assert isinstance(catalog_json, str)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(catalog_json + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} ({len(json.loads(catalog_json))} formats)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
