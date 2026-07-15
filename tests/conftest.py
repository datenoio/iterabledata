"""
Pytest configuration for iterable tests.
Ensures tests can find fixtures regardless of where pytest is run from.
"""

import os
import sys
from pathlib import Path

import pytest

# Get the tests directory
TESTS_DIR = Path(__file__).parent.absolute()

# Canonical committed fixture root (tests/testdata is a symlink to this directory)
FIXTURES_DIR = TESTS_DIR / "fixtures"

# Get the project root (parent of tests directory)
PROJECT_ROOT = TESTS_DIR.parent

# Add project root to Python path to ensure local code is used
# This prevents importing from installed packages when running tests
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Change to tests directory so relative paths work
# This ensures 'fixtures/...' and legacy 'testdata/...' paths work correctly
if os.getcwd() != str(TESTS_DIR):
    os.chdir(TESTS_DIR)

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
