#!/usr/bin/env python3
"""Ratchet the full-package Mypy error count against a committed baseline.

Runs ``mypy iterable`` (respecting ``pyproject.toml``), parses the summary
error count, and compares it against the integer recorded in
``dev/mypy_baseline.txt``:

- default mode prints current vs baseline and exits 1 when the count grew
  (no new typing errors), 0 otherwise;
- ``--update`` regenerates the baseline from the current run.

Counts are environment-sensitive: which optional dependencies are installed
changes the ``import-not-found``/attribute errors Mypy reports, so local runs
may differ from CI. CI is the reference environment — regenerate the baseline
from CI numbers (or a matching local toolchain) if it legitimately drifts.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "dev" / "mypy_baseline.txt"

_FOUND_RE = re.compile(r"^Found (\d+) errors? in \d+ files?", re.MULTILINE)


def run_mypy() -> int:
    """Run full-package mypy and return the summary error count."""
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "iterable"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    match = _FOUND_RE.search(result.stdout)
    if match:
        return int(match.group(1))
    if result.returncode == 0 and "Success: no issues found" in result.stdout:
        return 0
    print(result.stdout, file=sys.stderr)
    print(result.stderr, file=sys.stderr)
    msg = "could not parse the mypy summary line (mypy crashed or its output format changed)"
    raise RuntimeError(msg)


def read_baseline() -> int:
    """Return the first bare integer recorded in the baseline file."""
    for line in BASELINE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.isdigit():
            return int(stripped)
    msg = f"no integer baseline found in {BASELINE}"
    raise RuntimeError(msg)


def write_baseline(count: int) -> None:
    BASELINE.write_text(
        "# Full-package mypy error-count baseline for dev/scripts/mypy_ratchet.py.\n"
        "# Regenerate with: python dev/scripts/mypy_ratchet.py --update\n"
        "# Counts are environment-sensitive (optional deps); CI is the reference env.\n"
        f"# Updated: {date.today().isoformat()}\n"
        f"{count}\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update",
        action="store_true",
        help="Regenerate dev/mypy_baseline.txt from the current run.",
    )
    args = parser.parse_args(argv)

    if not args.update and not BASELINE.exists():
        print(f"No baseline at {BASELINE}; run with --update first.", file=sys.stderr)
        return 2

    try:
        current = run_mypy()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.update:
        write_baseline(current)
        print(f"Updated {BASELINE.relative_to(ROOT)} to {current} errors")
        return 0

    try:
        baseline = read_baseline()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"mypy full-package errors: current={current} baseline={baseline}")
    if current > baseline:
        print(
            f"FAIL: error count grew by {current - baseline} ({baseline} -> {current}). "
            "Fix the new errors, or regenerate with --update if the growth is an "
            "accepted environment artifact (CI is the reference env).",
            file=sys.stderr,
        )
        return 1
    if current < baseline:
        print(f"OK: no growth (improved by {baseline - current}; consider --update to lock in the progress)")
    else:
        print("OK: no growth (current == baseline)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
