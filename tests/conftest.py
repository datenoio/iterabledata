"""
Pytest configuration for iterable tests.
Ensures tests can find fixtures regardless of where pytest is run from.
"""

import dataclasses
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Get the tests directory
TESTS_DIR = Path(__file__).parent.absolute()

# Canonical committed fixture root (tests/testdata is a symlink to this directory)
CANONICAL_FIXTURES_DIR = TESTS_DIR / "fixtures"

# Get the project root (parent of tests directory)
PROJECT_ROOT = TESTS_DIR.parent

# Add project root to Python path to ensure local code is used
# This prevents importing from installed packages when running tests
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Legacy fixture path: many tests reference 'testdata/...'. The committed
# 'tests/testdata' is a symlink to 'tests/fixtures'. On checkouts made with
# core.symlinks=false (or when copied without symlink preservation) it can
# materialize as a regular file, which produces a large number of misleading
# FileExistsError/NotADirectoryError failures. Fail fast with an actionable
# message instead.
_TESTDATA_LINK = TESTS_DIR / "testdata"


def _verify_testdata_symlink() -> None:
    if _TESTDATA_LINK.is_symlink():
        return
    if not _TESTDATA_LINK.exists():
        # Best effort: recreate the expected symlink.
        try:
            _TESTDATA_LINK.symlink_to("fixtures")
            return
        except OSError:
            pass
    raise RuntimeError(
        f"'{_TESTDATA_LINK}' must be a symlink to 'tests/fixtures'. "
        "Your checkout materialized it as a regular file (common with "
        "core.symlinks=false). Restore it with: "
        "rm tests/testdata && ln -s fixtures tests/testdata"
    )


_verify_testdata_symlink()

# Fixture-generator scripts, not tests. ``--doctest-modules`` (addopts) would
# import them, and they need optional dependencies (pysam, protobuf) that most
# environments lack. ``testdata`` is a symlink to ``fixtures``, so the OTLP
# generator is reachable through both paths.
collect_ignore = [
    "create_bio_fixtures.py",
    "fixtures/otlp/generate_protobuf_fixtures.py",
    "testdata/otlp/generate_protobuf_fixtures.py",
]

# Tests historically write through the ``testdata`` compatibility path. Run
# against a disposable copy so committed fixtures remain immutable even when
# a legacy test has not yet been migrated to ``tmp_path``.
_RUNTIME_ROOT = Path(tempfile.mkdtemp(prefix="iterabledata-tests-"))
FIXTURES_DIR = _RUNTIME_ROOT / "fixtures"
shutil.copytree(CANONICAL_FIXTURES_DIR, FIXTURES_DIR)
(_RUNTIME_ROOT / "testdata").symlink_to("fixtures")


def pytest_configure(config):
    """Chdir to the disposable fixture root without breaking collection.

    Many tests open ``fixtures/...`` / ``testdata/...`` relative to the
    current working directory, so the session runs with ``_RUNTIME_ROOT``
    as cwd. Changing directory at conftest *import* time makes pytest
    resolve relative path arguments (e.g. ``pytest tests``) against the
    new cwd — under pytest-xdist workers that yields "0 items collected".
    Deferring the chdir to ``pytest_configure`` and first rewriting
    relative collection arguments to absolute paths keeps
    ``pytest -n auto`` working from the repo root.
    """
    invocation_dir = Path(config.invocation_params.dir)

    def _absolutize(arg):
        candidate = invocation_dir / str(arg)
        if not os.path.isabs(arg) and candidate.exists():
            return str(candidate)
        return arg

    positional = set(config.args)  # original (possibly relative) positional paths
    config.args[:] = [_absolutize(arg) for arg in config.args]
    # xdist hands ``invocation_params.args`` — the *full* raw command line,
    # options included, as an immutable tuple — to its workers. Rewrite only
    # the tokens pytest itself parsed as positional paths and preserve every
    # option verbatim: dropping flags here breaks plugins that re-parse the
    # raw args on the worker (e.g. pytest-cov's --no-cov detection).
    # ``InvocationParams`` is a frozen dataclass (pytest >= 7.3), not a
    # NamedTuple: it has no ``_replace``, and the ``__replace__`` hook only
    # exists on Python 3.13+, so use ``dataclasses.replace``.
    rewritten = tuple(_absolutize(arg) if arg in positional else arg for arg in config.invocation_params.args)
    config.invocation_params = dataclasses.replace(config.invocation_params, args=rewritten)
    os.chdir(_RUNTIME_ROOT)


def fixture_path(name: str) -> Path:
    """Return an absolute path under ``tests/fixtures/``."""
    return FIXTURES_DIR / name


@pytest.fixture(autouse=True, scope="session")
def ensure_testdata_dir():
    """Ensure the fixtures directory exists for all tests."""
    FIXTURES_DIR.mkdir(exist_ok=True)
    return FIXTURES_DIR


@pytest.fixture(autouse=True)
def _reset_iterable_logging():
    """Reset IterableData's logger hierarchy after each test.

    ``enable_debug_mode`` attaches handlers and sets ``propagate = False`` on the
    package loggers (notably the root ``iterable`` logger). Without a reset that
    global state leaks across tests and, for example, prevents pytest's ``caplog``
    fixture from capturing records emitted by child loggers. Restoring the loggers
    after every test keeps tests isolated from one another.
    """
    import logging

    yield

    for name in ("iterable", "iterable.detect", "iterable.io", "iterable.parse", "iterable.perf"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True
        lg.setLevel(logging.NOTSET)


def pytest_addoption(parser):
    """Register custom options used by the performance regression suite.

    pytest only collects ``pytest_addoption`` from conftest plugins, so these
    must live here rather than in ``test_performance_regression.py``.
    """
    parser.addoption(
        "--update-baselines",
        action="store_true",
        default=False,
        help="Update baseline performance metrics",
    )
    parser.addoption(
        "--skip-regression",
        action="store_true",
        default=False,
        help="Skip regression checks (run benchmarks only)",
    )
