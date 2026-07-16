#!/usr/bin/env python3
"""Export dev/formats.json from iterable.catalog."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "dev" / "formats.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check committed output without rewriting it")
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    from iterable.catalog import export_catalog

    catalog_json = export_catalog(format="json", include_capabilities=True)
    assert isinstance(catalog_json, str)
    rendered = catalog_json + "\n"
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != rendered:
            raise SystemExit(f"{OUTPUT} is stale; run dev/scripts/export_formats_json.py")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(rendered, encoding="utf-8")
    action = "Checked" if args.check else "Wrote"
    print(f"{action} {OUTPUT} ({len(json.loads(catalog_json))} formats)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
