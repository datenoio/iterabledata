#!/usr/bin/env python3
"""Fail if files changed vs a base ref introduce Mypy errors (new-code strictness).

Computes ``git diff --name-only <base>...HEAD -- 'iterable/*.py'`` (excluding
deleted files) and runs Mypy over exactly those files with the repo's standard
configuration (``pyproject.toml`` is picked up automatically) plus
``--follow-imports=skip``, matching the blocking core gate in CI: errors are
reported for the changed files themselves, not for their (possibly legacy)
imported dependencies.

Usage:
    python dev/scripts/mypy_changed_files.py [BASE_REF]

BASE_REF defaults to ``origin/main``, falling back to ``main`` when no remote
tracking ref exists. Exit codes: 0 = no changed files or no errors in them,
1 = errors found in changed files, 2 = the check itself could not run (bad
ref, missing merge base, mypy crash).

CI note: the checkout must fetch enough history for the three-dot merge-base
diff (``actions/checkout`` with ``fetch-depth: 0``).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATHSPEC = "iterable/*.py"
DEFAULT_BASES = ("origin/main", "main")


def git(*args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=check,
    )


def resolve_base(argv: list[str]) -> str:
    """Return the requested base ref, or the first default that exists."""
    if argv:
        base = argv[0]
        if git("rev-parse", "--verify", "--quiet", base).returncode != 0:
            print(f"ERROR: base ref '{base}' does not exist", file=sys.stderr)
            raise SystemExit(2)
        return base
    for candidate in DEFAULT_BASES:
        if git("rev-parse", "--verify", "--quiet", candidate).returncode == 0:
            return candidate
    print(
        f"ERROR: none of the default base refs {DEFAULT_BASES} exist; pass a base ref explicitly",
        file=sys.stderr,
    )
    raise SystemExit(2)


def changed_files(base: str) -> list[str]:
    """Return iterable/*.py files (excluding deletions) changed vs the merge base."""
    result = git(
        "diff",
        "--name-only",
        "--diff-filter=d",
        f"{base}...HEAD",
        "--",
        PATHSPEC,
    )
    if result.returncode != 0:
        print(
            f"ERROR: 'git diff {base}...HEAD' failed (missing merge base? "
            "fetch full history, e.g. actions/checkout fetch-depth: 0):\n"
            f"{result.stderr.strip()}",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return [line for line in result.stdout.splitlines() if line.strip()]


def run_mypy(files: list[str]) -> int:
    """Run mypy over the changed files and return its exit code."""
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--follow-imports=skip", *files],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    base = resolve_base(args)
    files = changed_files(base)
    if not files:
        print(f"OK: no '{PATHSPEC}' files changed vs {base}; nothing to check")
        return 0

    print(f"Checking {len(files)} changed file(s) vs {base} with mypy:")
    for path in files:
        print(f"  {path}")

    code = run_mypy(files)
    if code == 0:
        print("OK: no mypy errors in changed files")
        return 0
    if code == 1:
        print(
            "FAIL: mypy errors in files changed on this branch. "
            "New and touched code must type-check cleanly; fix the errors above.",
            file=sys.stderr,
        )
        return 1
    print(f"ERROR: mypy exited with code {code} (crash, not findings)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
