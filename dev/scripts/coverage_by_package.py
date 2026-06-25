#!/usr/bin/env python3
"""Print per-package coverage breakdown from an existing ``.coverage`` data file.

Baseline floors are advisory thresholds (plan §4.4). Use ``--check`` to exit
non-zero when any package drops below its floor — intended for gradual CI
hardening, not blocking yet.
"""

from __future__ import annotations

import argparse
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

# Advisory floors — raise as coverage improves (global target remains 75 → 85).
PACKAGE_FLOORS: dict[str, float] = {
    "datatypes": 50.0,
    "helpers": 75.0,
    "codecs": 60.0,
    "engines": 55.0,
    "ingest": 45.0,
    "convert": 70.0,
    "db": 65.0,
    "ops": 75.0,
    "pipeline": 75.0,
}

_TOTAL_RE = re.compile(r"^TOTAL\s+.+?\s+(\d+(?:\.\d+)?)%", re.MULTILINE)


def _report_include(include: str) -> float | None:
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
    return float(match.group(1)) if match else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if any package is below its advisory floor.",
    )
    args = parser.parse_args(argv)

    if not (ROOT / ".coverage").exists():
        print(
            "No .coverage data found. Run pytest with --cov=iterable first.",
            file=sys.stderr,
        )
        return 1

    print("=" * 40)
    print("PER-PACKAGE COVERAGE")
    print("=" * 40)

    below_floor: list[tuple[str, float, float]] = []

    for include, label in PACKAGES:
        pct = _report_include(include)
        floor = PACKAGE_FLOORS.get(label)
        if pct is None:
            print(f"{label:<14} (no data)")
            continue
        floor_note = f" (floor {floor:.0f}%)" if floor is not None else ""
        status = ""
        if floor is not None and pct < floor:
            status = " BELOW FLOOR"
            below_floor.append((label, pct, floor))
        print(f"{label:<14} {pct:>5.2f}%{floor_note}{status}")

    print("=" * 40)

    if below_floor:
        print("Packages below advisory floor:", file=sys.stderr)
        for label, pct, floor in below_floor:
            print(f"  {label}: {pct:.2f}% < {floor:.0f}%", file=sys.stderr)
        if args.check:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
