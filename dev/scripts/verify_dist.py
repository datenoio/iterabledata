"""Verify that built distributions contain only intended package paths and every runtime resource."""

from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path

ALLOWED_PREFIXES = ("iterable/",)
METADATA_SUFFIXES = (".dist-info/", ".dist-info", ".egg-info/", ".egg-info")
ALLOWED_FILES = (
    "README.md",
    "LICENSE",
    "LICENSE.txt",
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
    "PKG-INFO",
    "SOURCES.txt",
    "MANIFEST.in",
)


def _allowed(name: str) -> bool:
    normalized = name.lstrip("./")
    candidates = [normalized]
    if "/" in normalized:
        candidates.append(normalized.split("/", 1)[1])
    for candidate in candidates:
        if candidate in ALLOWED_FILES or candidate.startswith(ALLOWED_FILES):
            return True
        if candidate == "iterable" or candidate.startswith(ALLOWED_PREFIXES):
            return True
        if any(suffix in candidate for suffix in METADATA_SUFFIXES):
            return True
    # A source distribution has one package-version directory at its root.
    return "/" not in normalized and normalized.startswith("iterabledata-")


REPO_ROOT = Path(__file__).resolve().parents[2]


def runtime_resources(root: Path = REPO_ROOT) -> list[str]:
    """Non-Python files under ``iterable/`` that the installed package reads at runtime."""
    package = root / "iterable"
    return sorted(
        path.relative_to(root).as_posix()
        for path in package.rglob("*")
        if path.is_file() and path.suffix not in (".py", ".pyc") and "__pycache__" not in path.parts
    )


def _missing_resources(names: list[str]) -> list[str]:
    # sdist members live under one ``iterabledata-<version>/`` directory; wheel members do not.
    present = {name.partition("/")[2] if name.startswith("iterabledata-") else name for name in names}
    return [resource for resource in runtime_resources() if resource not in present]


def verify(path: Path) -> None:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
    elif path.name.endswith((".tar.gz", ".tar.bz2", ".tar.xz", ".tgz")):
        with tarfile.open(path) as archive:
            names = archive.getnames()
    else:
        raise ValueError(f"Unsupported distribution: {path}")

    unexpected = [name for name in names if not _allowed(name)]
    if unexpected:
        raise SystemExit(f"Unexpected top-level distribution paths in {path}: {unexpected[:10]}")
    missing = _missing_resources(names)
    if missing:
        raise SystemExit(f"Runtime resources missing from {path}: {missing}")


def main() -> int:
    distributions = [Path(arg) for arg in sys.argv[1:]]
    if not distributions:
        distributions = sorted(Path("dist").glob("*.whl")) + sorted(Path("dist").glob("*.tar.gz"))
    if not distributions:
        raise SystemExit("No distribution artifacts found")
    for distribution in distributions:
        verify(distribution)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
