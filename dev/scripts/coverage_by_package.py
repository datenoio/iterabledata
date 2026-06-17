#!/usr/bin/env python3
"""Print per-package coverage breakdown from an existing ``.coverage`` data file."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PACKAGES = (
    ("iterable/datatypes/*", "datatypes"),
    ("iterable/helpers/*", "helpers"),
    ("iterable/codecs/*", "codecs"),
    ("iterable/engines/*", "engines"),
    ("iterable/ingest/*", "ingest"),
    ("iterable/convert/*", "convert"),
    ("iterable/db/*", "db"),
    ("iterable/ops/*", "ops"),
    ("iterable/pipeline/*", "pipeline"),
)

_TOTAL_RE = re.compile(r"^TOTAL\s+.+?\s+(\d+(?:\.\d+)?)%", re.MULTILINE)


def _report_include(include: str) -> str | None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "coverage",
            "report",
            f"--include={include}",
            "--fail-under=0",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 1, 2):
        return None
    match = _TOTAL_RE.search(result.stdout)
    return match.group(1) if match else None


def main() -> int:
    if not (ROOT / ".coverage").exists():
        print(
            "No .coverage data found. Run pytest with --cov=iterable first.",
            file=sys.stderr,
        )
        return 1

    print("=" * 40)
    print("PER-PACKAGE COVERAGE")
    print("=" * 40)

    for include, label in PACKAGES:
        pct = _report_include(include)
        if pct is None:
            print(f"{label:<14} (no data)")
        else:
            print(f"{label:<14} {pct}%")

    print("=" * 40)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
