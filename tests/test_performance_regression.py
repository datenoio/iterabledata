"""Enforced performance regression gate for IterableData.

Representative workloads (CSV read, JSONL read, compressed JSONL -> Parquet
convert, bulk read/write) are timed and compared against committed baselines
in ``tests/performance_baselines.json``.

To make baselines portable across machines, every measurement is normalized
by a fixed pure-Python calibration workload timed in the same session. The
committed baseline for a workload is therefore a machine-independent ratio
(workload time / calibration time), and tolerances are generous to absorb
residual noise.

Running the gate (the ``performance`` marker is excluded by default):

    pytest tests/test_performance_regression.py -m performance --no-cov

Regenerating baselines (do this intentionally, on the reference environment,
when a change legitimately alters performance; commit the resulting JSON):

    pytest tests/test_performance_regression.py -m performance --no-cov \
        --update-baselines

Behavior when the baseline file is missing:
- in CI (``CI`` env var set): the gate FAILS with regeneration instructions
- locally: the test is skipped

Set ``ITERABLE_PERF_BASELINE_FILE`` to point the gate at an alternative
baseline file (used for validating that the gate detects regressions).
"""

import gzip
import json
import os
import platform
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from iterable.convert import convert
from iterable.helpers.detect import open_iterable

pytestmark = pytest.mark.performance

DEFAULT_BASELINE_FILE = Path(__file__).parent / "performance_baselines.json"

ROWS = 10_000
WARMUP_RUNS = 1
MEASURED_RUNS = 3

# Explicit per-workload tolerance multipliers applied to the committed
# normalized baseline. E.g. 2.0 means "fail only when more than 2x slower
# (relative to the calibration workload) than the reference measurement".
TOLERANCES = {
    "csv_read_10k": 2.0,
    "jsonl_read_10k": 2.0,
    "csv_bulk_read_10k": 2.0,
    "csv_bulk_write_10k": 2.0,
    "jsonl_gz_to_parquet_convert_10k": 2.5,
}


def _baseline_file() -> Path:
    override = os.environ.get("ITERABLE_PERF_BASELINE_FILE")
    return Path(override) if override else DEFAULT_BASELINE_FILE


def load_baselines() -> dict[str, Any]:
    path = _baseline_file()
    if not path.exists():
        return {}
    with path.open("r") as f:
        return json.load(f)


def save_baseline(key: str, normalized: float) -> None:
    path = _baseline_file()
    data = load_baselines()
    data.setdefault("_meta", {}).update(
        {
            "description": (
                "Normalized performance baselines: workload wall time divided by "
                "a pure-Python calibration workload timed on the same machine. "
                "Regenerate with: pytest tests/test_performance_regression.py "
                "-m performance --no-cov --update-baselines"
            ),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "rows": ROWS,
        }
    )
    data.setdefault("workloads", {})[key] = round(normalized, 4)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def _best_of(func: Callable[[], Any], runs: int = MEASURED_RUNS, warmup: int = WARMUP_RUNS) -> float:
    """Return the best wall time of ``runs`` executions after ``warmup`` runs."""
    for _ in range(warmup):
        func()
    best = float("inf")
    for _ in range(runs):
        start = time.perf_counter()
        func()
        best = min(best, time.perf_counter() - start)
    return best


def _calibration_workload() -> int:
    """Fixed pure-Python workload used to normalize timings across machines."""
    total = 0
    for i in range(1_500_000):
        total += i * i
    return total


@pytest.fixture(scope="module")
def calibration_time() -> float:
    return _best_of(_calibration_workload)


@pytest.fixture(scope="module")
def workload_files(tmp_path_factory):
    """Create the shared input files for all workloads once per module."""
    root = tmp_path_factory.mktemp("perf")

    csv_file = root / "data.csv"
    with csv_file.open("w") as f:
        f.write("id,name,value\n")
        for i in range(ROWS):
            f.write(f"{i},Name{i},{i * 10}\n")

    jsonl_file = root / "data.jsonl"
    with jsonl_file.open("w") as f:
        for i in range(ROWS):
            f.write(json.dumps({"id": i, "name": f"Name{i}", "value": i * 10}) + "\n")

    jsonl_gz_file = root / "data.jsonl.gz"
    with gzip.open(jsonl_gz_file, "wt") as f:
        for i in range(ROWS):
            f.write(json.dumps({"id": i, "name": f"Name{i}", "value": i * 10}) + "\n")

    return {"root": root, "csv": csv_file, "jsonl": jsonl_file, "jsonl_gz": jsonl_gz_file}


def _check_workload(key: str, func: Callable[[], Any], calibration_time: float, request) -> None:
    """Measure one workload and compare its normalized time to the baseline."""
    if request.config.getoption("--skip-regression"):
        pytest.skip("Regression check skipped via --skip-regression")

    elapsed = _best_of(func)
    normalized = elapsed / calibration_time

    if request.config.getoption("--update-baselines"):
        save_baseline(key, normalized)
        pytest.skip(f"Baseline updated: {key} = {normalized:.4f}")

    baselines = load_baselines().get("workloads", {})
    baseline = baselines.get(key)
    if baseline is None:
        message = (
            f"No committed baseline for workload '{key}' in {_baseline_file()}. "
            "Regenerate with: pytest tests/test_performance_regression.py "
            "-m performance --no-cov --update-baselines"
        )
        if os.environ.get("CI"):
            pytest.fail(message)
        pytest.skip(message)

    tolerance = TOLERANCES[key]
    max_acceptable = baseline * tolerance
    assert normalized <= max_acceptable, (
        f"Performance regression in workload '{key}': normalized time "
        f"{normalized:.4f} exceeds {max_acceptable:.4f} "
        f"(baseline {baseline:.4f} x tolerance {tolerance}). "
        f"Raw: workload {elapsed:.4f}s, calibration {calibration_time:.4f}s."
    )


class TestPerformanceRegressionGate:
    """Compare representative workloads against committed baselines."""

    def test_csv_read(self, workload_files, calibration_time, request):
        def workload():
            with open_iterable(workload_files["csv"]) as source:
                for _row in source:
                    pass

        _check_workload("csv_read_10k", workload, calibration_time, request)

    def test_jsonl_read(self, workload_files, calibration_time, request):
        def workload():
            with open_iterable(workload_files["jsonl"]) as source:
                for _row in source:
                    pass

        _check_workload("jsonl_read_10k", workload, calibration_time, request)

    def test_csv_bulk_read(self, workload_files, calibration_time, request):
        def workload():
            with open_iterable(workload_files["csv"]) as source:
                while source.read_bulk(num=1000):
                    pass

        _check_workload("csv_bulk_read_10k", workload, calibration_time, request)

    def test_csv_bulk_write(self, workload_files, calibration_time, request):
        data = [{"id": i, "name": f"Name{i}", "value": i * 10} for i in range(ROWS)]
        output = workload_files["root"] / "bulk_out.csv"

        def workload():
            with open_iterable(output, "w") as dest:
                dest.write_bulk(data)

        _check_workload("csv_bulk_write_10k", workload, calibration_time, request)

    def test_jsonl_gz_to_parquet_convert(self, workload_files, calibration_time, request):
        pytest.importorskip("pyarrow", reason="Parquet convert workload requires pyarrow")
        output = workload_files["root"] / "converted.parquet"

        def workload():
            convert(str(workload_files["jsonl_gz"]), str(output))

        _check_workload("jsonl_gz_to_parquet_convert_10k", workload, calibration_time, request)
