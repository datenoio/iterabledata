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

# Get the project root (parent of tests directory)
PROJECT_ROOT = TESTS_DIR.parent

# Add project root to Python path to ensure local code is used
# This prevents importing from installed packages when running tests
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Change to tests directory so relative paths work
# This ensures 'fixtures/...' paths work correctly
if os.getcwd() != str(TESTS_DIR):
    os.chdir(TESTS_DIR)


@pytest.fixture(autouse=True, scope="session")
def ensure_testdata_dir():
    """Ensure testdata directory exists for all tests."""
    testdata_dir = TESTS_DIR / "testdata"
    testdata_dir.mkdir(exist_ok=True)
    return testdata_dir


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
