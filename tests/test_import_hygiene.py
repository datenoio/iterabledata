"""Import hygiene: a light ``import iterable``, lazy database drivers, ``iterable.ai`` binding, packaged resources."""

import fnmatch
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

try:
    import tomllib
except ImportError:  # Python 3.10
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]

# Optional backends that ``import iterable`` must not load.
HEAVY_MODULES = ("elasticsearch", "pymongo", "pyarrow", "numpy", "pandas", "duckdb", "httpx", "requests", "rich")


def _run(code: str) -> dict:
    """Run ``code`` in a fresh interpreter importing this checkout; return the JSON it prints."""
    python_path = os.pathsep.join(filter(None, [str(REPO_ROOT), os.environ.get("PYTHONPATH")]))
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": python_path},
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_package_import_skips_optional_backends():
    loaded = _run(
        f"import json, sys, iterable\nprint(json.dumps(sorted(m for m in {HEAVY_MODULES!r} if m in sys.modules)))"
    )
    assert loaded == []


def test_database_driver_imported_on_first_use():
    state = _run(
        "import json, sys\n"
        "from iterable.db import get_driver, is_database_engine, list_drivers\n"
        "before = sorted(m for m in sys.modules if m.startswith('iterable.db.'))\n"
        "driver = get_driver('sqlite')\n"
        "after = sorted(m for m in sys.modules if m.startswith('iterable.db.'))\n"
        "print(json.dumps({'before': before, 'after': after, 'driver': driver.__name__,\n"
        "    'is_engine': is_database_engine('elasticsearch'), 'listed': 'mongo' in list_drivers()}))"
    )
    assert "iterable.db.sqlite" not in state["before"]
    assert "iterable.db.sqlite" in state["after"]
    assert "iterable.db.elasticsearch" not in state["after"]
    assert state["driver"] == "SQLiteDriver"
    assert state["is_engine"] is True
    assert state["listed"] is True


def test_detect_keeps_driver_names():
    from iterable.db.postgres import PostgresDriver
    from iterable.helpers import detect

    assert detect.PostgresDriver is PostgresDriver
    with mock.patch("iterable.helpers.detect.ClickHouseDriver") as patched:
        assert detect.ClickHouseDriver is patched


def test_builtin_driver_names_cannot_be_reregistered():
    from iterable.db import DBDriver, register_driver

    class Shadow(DBDriver):
        def connect(self):
            pass

        def iterate(self):
            yield {}

    with pytest.raises(ValueError, match="already registered"):
        register_driver("postgres", Shadow)


def test_ai_attribute_is_the_package():
    pytest.importorskip("requests", reason="AI extras are not installed")
    import iterable
    import iterable.ai.doc

    assert iterable.ai.__name__ == "iterable.ai"
    assert sys.modules["iterable.ai"] is iterable.ai
    assert iterable.ai.generate is iterable.ai.doc.generate
    with mock.patch("iterable.ai.providers.get_provider") as patched:
        assert iterable.ai.providers.get_provider is patched


def test_package_data_covers_runtime_resources():
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    patterns = config["tool"]["setuptools"]["package-data"]["iterable"]
    package = REPO_ROOT / "iterable"
    resources = [
        path.relative_to(package).as_posix()
        for path in package.rglob("*")
        if path.is_file() and path.suffix not in (".py", ".pyc") and "__pycache__" not in path.parts
    ]
    assert "ai/prompts/documentation.txt" in resources
    uncovered = [r for r in resources if not any(fnmatch.fnmatch(r, p) for p in patterns)]
    assert uncovered == [], f"Add these to [tool.setuptools.package-data] and MANIFEST.in: {uncovered}"
