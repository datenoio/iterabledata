"""Performance regression tests for IterableData.

These tests compare current performance against baseline metrics to detect
performance regressions. They fail if performance degrades beyond acceptable thresholds.

Baseline metrics are stored in a JSON file and can be updated when performance
improvements are made.

Run with: pytest tests/test_performance_regression.py -v

To update baselines after performance improvements:
    pytest tests/test_performance_regression.py --update-baselines

To skip regression tests (run benchmarks only):
    pytest tests/test_performance_regression.py --skip-regression
"""

import json
import time
from pathlib import Path
from typing import Any

import pytest

from iterable.datatypes.csv import CSVIterable
from iterable.helpers.detect import open_iterable

# Baseline file location
BASELINE_FILE = Path(__file__).parent / "performance_baselines.json"

# Performance regression thresholds (as multipliers)
# e.g., 1.2 means 20% slower is acceptable, 1.5 means 50% slower fails
PERFORMANCE_THRESHOLDS = {
    "csv_read_small": 1.2,  # 20% slower acceptable
    "csv_read_medium": 1.2,
    "csv_read_large": 1.3,  # 30% slower acceptable for large files
    "csv_write_small": 1.2,
    "csv_write_medium": 1.2,
    "jsonl_read_small": 1.2,
    "jsonl_read_medium": 1.2,
    "jsonl_write_small": 1.2,
    "format_detection": 1.2,
    "bulk_read_small": 1.15,  # 15% slower acceptable (should be fast)
    "bulk_read_medium": 1.2,
    "bulk_write_small": 1.15,
    "factory_method_init": 1.1,  # 10% slower acceptable (should be minimal overhead)
    "streaming_read": 1.2,
    "reset_operation": 1.2,
}


def load_baselines() -> dict[str, float]:
    """Load baseline performance metrics from file."""
    if not BASELINE_FILE.exists():
        return {}

    try:
        with BASELINE_FILE.open("r") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_baselines(baselines: dict[str, float]) -> None:
    """Save baseline performance metrics to file."""
    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with BASELINE_FILE.open("w") as f:
        json.dump(baselines, f, indent=2)


def measure_operation(func: Any, *args: Any, **kwargs: Any) -> float:
    """Measure execution time of an operation in seconds."""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - start
    # Consume result if it's an iterator
    if hasattr(result, "__iter__") and not isinstance(result, (str, bytes)):
        try:
            list(result)
        except Exception:
            pass
    return elapsed


@pytest.fixture
def small_csv_data(tmp_path):
    """Create a small CSV file for testing (100 rows)."""
    test_file = tmp_path / "small.csv"
    lines = ["id,name,value"] + [f"{i},Name{i},{i * 10}" for i in range(100)]
    test_file.write_text("\n".join(lines))
    return test_file


@pytest.fixture
def medium_csv_data(tmp_path):
    """Create a medium CSV file for testing (10,000 rows)."""
    test_file = tmp_path / "medium.csv"
    lines = ["id,name,value"]
    with test_file.open("w") as f:
        f.write("\n".join(lines) + "\n")
        for i in range(10000):
            f.write(f"{i},Name{i},{i * 10}\n")
    return test_file


@pytest.fixture
def small_jsonl_data(tmp_path):
    """Create a small JSONL file for testing (100 rows)."""
    import json

    test_file = tmp_path / "small.jsonl"
    with test_file.open("w") as f:
        for i in range(100):
            f.write(json.dumps({"id": i, "name": f"Name{i}", "value": i * 10}) + "\n")
    return test_file


@pytest.fixture
def medium_jsonl_data(tmp_path):
    """Create a medium JSONL file for testing (10,000 rows)."""
    import json

    test_file = tmp_path / "medium.jsonl"
    with test_file.open("w") as f:
        for i in range(10000):
            f.write(json.dumps({"id": i, "name": f"Name{i}", "value": i * 10}) + "\n")
    return test_file


# NOTE: pytest options (--update-baselines, --skip-regression) are registered
# in tests/conftest.py, since pytest only collects pytest_addoption from conftest.


class TestCSVPerformanceRegression:
    """Test CSV read/write performance regression."""

    def test_csv_read_small_performance(self, small_csv_data, request):
        """Test CSV read performance for small files."""
        baselines = load_baselines()
        update_baselines = request.config.getoption("--update-baselines")
        skip_regression = request.config.getoption("--skip-regression")

        elapsed = measure_operation(lambda: list(open_iterable(small_csv_data)))

        baseline_key = "csv_read_small"
        baseline = baselines.get(baseline_key)

        if update_baselines:
            baselines[baseline_key] = elapsed
            save_baselines(baselines)
            pytest.skip("Baseline updated")

        if skip_regression or baseline is None:
            pytest.skip("No baseline available or regression check skipped")

        threshold = PERFORMANCE_THRESHOLDS.get(baseline_key, 1.2)
        max_acceptable = baseline * threshold

        assert elapsed <= max_acceptable, (
            f"CSV read performance regressed: {elapsed:.4f}s > {max_acceptable:.4f}s "
            f"(baseline: {baseline:.4f}s, threshold: {threshold}x)"
        )

    def test_csv_read_medium_performance(self, medium_csv_data, request):
        """Test CSV read performance for medium files."""
        baselines = load_baselines()
        update_baselines = request.config.getoption("--update-baselines")
        skip_regression = request.config.getoption("--skip-regression")

        elapsed = measure_operation(lambda: list(open_iterable(medium_csv_data)))

        baseline_key = "csv_read_medium"
        baseline = baselines.get(baseline_key)

        if update_baselines:
            baselines[baseline_key] = elapsed
            save_baselines(baselines)
            pytest.skip("Baseline updated")

        if skip_regression or baseline is None:
            pytest.skip("No baseline available or regression check skipped")

        threshold = PERFORMANCE_THRESHOLDS.get(baseline_key, 1.2)
        max_acceptable = baseline * threshold

        assert elapsed <= max_acceptable, (
            f"CSV read (medium) performance regressed: {elapsed:.4f}s > {max_acceptable:.4f}s "
            f"(baseline: {baseline:.4f}s, threshold: {threshold}x)"
        )

    def test_csv_write_small_performance(self, tmp_path, request):
        """Test CSV write performance for small files."""
        baselines = load_baselines()
        update_baselines = request.config.getoption("--update-baselines")
        skip_regression = request.config.getoption("--skip-regression")

        output_file = tmp_path / "output.csv"
        data = [{"id": i, "name": f"Name{i}", "value": i * 10} for i in range(100)]

        def write_operation():
            with open_iterable(output_file, "w") as dest:
                dest.write_bulk(data)

        elapsed = measure_operation(write_operation)

        baseline_key = "csv_write_small"
        baseline = baselines.get(baseline_key)

        if update_baselines:
            baselines[baseline_key] = elapsed
            save_baselines(baselines)
            pytest.skip("Baseline updated")

        if skip_regression or baseline is None:
            pytest.skip("No baseline available or regression check skipped")

        threshold = PERFORMANCE_THRESHOLDS.get(baseline_key, 1.2)
        max_acceptable = baseline * threshold

        assert elapsed <= max_acceptable, (
            f"CSV write performance regressed: {elapsed:.4f}s > {max_acceptable:.4f}s "
            f"(baseline: {baseline:.4f}s, threshold: {threshold}x)"
        )

    def test_csv_write_medium_performance(self, tmp_path, request):
        """Test CSV write performance for medium files."""
        baselines = load_baselines()
        update_baselines = request.config.getoption("--update-baselines")
        skip_regression = request.config.getoption("--skip-regression")

        output_file = tmp_path / "output.csv"
        data = [{"id": i, "name": f"Name{i}", "value": i * 10} for i in range(10000)]

        def write_operation():
            with open_iterable(output_file, "w") as dest:
                dest.write_bulk(data)

        elapsed = measure_operation(write_operation)

        baseline_key = "csv_write_medium"
        baseline = baselines.get(baseline_key)

        if update_baselines:
            baselines[baseline_key] = elapsed
            save_baselines(baselines)
            pytest.skip("Baseline updated")

        if skip_regression or baseline is None:
            pytest.skip("No baseline available or regression check skipped")

        threshold = PERFORMANCE_THRESHOLDS.get(baseline_key, 1.2)
        max_acceptable = baseline * threshold

        assert elapsed <= max_acceptable, (
            f"CSV write (medium) performance regressed: {elapsed:.4f}s > {max_acceptable:.4f}s "
            f"(baseline: {baseline:.4f}s, threshold: {threshold}x)"
        )


class TestJSONLPerformanceRegression:
    """Test JSONL read/write performance regression."""

    def test_jsonl_read_small_performance(self, small_jsonl_data, request):
        """Test JSONL read performance for small files."""
        baselines = load_baselines()
        update_baselines = request.config.getoption("--update-baselines")
        skip_regression = request.config.getoption("--skip-regression")

        elapsed = measure_operation(lambda: list(open_iterable(small_jsonl_data)))

        baseline_key = "jsonl_read_small"
        baseline = baselines.get(baseline_key)

        if update_baselines:
            baselines[baseline_key] = elapsed
            save_baselines(baselines)
            pytest.skip("Baseline updated")

        if skip_regression or baseline is None:
            pytest.skip("No baseline available or regression check skipped")

        threshold = PERFORMANCE_THRESHOLDS.get(baseline_key, 1.2)
        max_acceptable = baseline * threshold

        assert elapsed <= max_acceptable, (
            f"JSONL read performance regressed: {elapsed:.4f}s > {max_acceptable:.4f}s "
            f"(baseline: {baseline:.4f}s, threshold: {threshold}x)"
        )

    def test_jsonl_read_medium_performance(self, medium_jsonl_data, request):
        """Test JSONL read performance for medium files."""
        baselines = load_baselines()
        update_baselines = request.config.getoption("--update-baselines")
        skip_regression = request.config.getoption("--skip-regression")

        elapsed = measure_operation(lambda: list(open_iterable(medium_jsonl_data)))

        baseline_key = "jsonl_read_medium"
        baseline = baselines.get(baseline_key)

        if update_baselines:
            baselines[baseline_key] = elapsed
            save_baselines(baselines)
            pytest.skip("Baseline updated")

        if skip_regression or baseline is None:
            pytest.skip("No baseline available or regression check skipped")

        threshold = PERFORMANCE_THRESHOLDS.get(baseline_key, 1.2)
        max_acceptable = baseline * threshold

        assert elapsed <= max_acceptable, (
            f"JSONL read (medium) performance regressed: {elapsed:.4f}s > {max_acceptable:.4f}s "
            f"(baseline: {baseline:.4f}s, threshold: {threshold}x)"
        )

    def test_jsonl_write_small_performance(self, tmp_path, request):
        """Test JSONL write performance for small files."""
        baselines = load_baselines()
        update_baselines = request.config.getoption("--update-baselines")
        skip_regression = request.config.getoption("--skip-regression")

        output_file = tmp_path / "output.jsonl"
        data = [{"id": i, "name": f"Name{i}", "value": i * 10} for i in range(100)]

        def write_operation():
            with open_iterable(output_file, "w") as dest:
                dest.write_bulk(data)

        elapsed = measure_operation(write_operation)

        baseline_key = "jsonl_write_small"
        baseline = baselines.get(baseline_key)

        if update_baselines:
            baselines[baseline_key] = elapsed
            save_baselines(baselines)
            pytest.skip("Baseline updated")

        if skip_regression or baseline is None:
            pytest.skip("No baseline available or regression check skipped")

        threshold = PERFORMANCE_THRESHOLDS.get(baseline_key, 1.2)
        max_acceptable = baseline * threshold

        assert elapsed <= max_acceptable, (
            f"JSONL write performance regressed: {elapsed:.4f}s > {max_acceptable:.4f}s "
            f"(baseline: {baseline:.4f}s, threshold: {threshold}x)"
        )


class TestBulkOperationsPerformanceRegression:
    """Test bulk operations performance regression."""

    def test_bulk_read_small_performance(self, small_csv_data, request):
        """Test bulk read performance for small files."""
        baselines = load_baselines()
        update_baselines = request.config.getoption("--update-baselines")
        skip_regression = request.config.getoption("--skip-regression")

        def bulk_read_operation():
            with open_iterable(small_csv_data) as source:
                while True:
                    chunk = source.read_bulk(num=10)
                    if not chunk:
                        break

        elapsed = measure_operation(bulk_read_operation)

        baseline_key = "bulk_read_small"
        baseline = baselines.get(baseline_key)

        if update_baselines:
            baselines[baseline_key] = elapsed
            save_baselines(baselines)
            pytest.skip("Baseline updated")

        if skip_regression or baseline is None:
            pytest.skip("No baseline available or regression check skipped")

        threshold = PERFORMANCE_THRESHOLDS.get(baseline_key, 1.15)
        max_acceptable = baseline * threshold

        assert elapsed <= max_acceptable, (
            f"Bulk read performance regressed: {elapsed:.4f}s > {max_acceptable:.4f}s "
            f"(baseline: {baseline:.4f}s, threshold: {threshold}x)"
        )

    def test_bulk_read_medium_performance(self, medium_csv_data, request):
        """Test bulk read performance for medium files."""
        baselines = load_baselines()
        update_baselines = request.config.getoption("--update-baselines")
        skip_regression = request.config.getoption("--skip-regression")

        def bulk_read_operation():
            with open_iterable(medium_csv_data) as source:
                while True:
                    chunk = source.read_bulk(num=1000)
                    if not chunk:
                        break

        elapsed = measure_operation(bulk_read_operation)

        baseline_key = "bulk_read_medium"
        baseline = baselines.get(baseline_key)

        if update_baselines:
            baselines[baseline_key] = elapsed
            save_baselines(baselines)
            pytest.skip("Baseline updated")

        if skip_regression or baseline is None:
            pytest.skip("No baseline available or regression check skipped")

        threshold = PERFORMANCE_THRESHOLDS.get(baseline_key, 1.2)
        max_acceptable = baseline * threshold

        assert elapsed <= max_acceptable, (
            f"Bulk read (medium) performance regressed: {elapsed:.4f}s > {max_acceptable:.4f}s "
            f"(baseline: {baseline:.4f}s, threshold: {threshold}x)"
        )

    def test_bulk_write_small_performance(self, tmp_path, request):
        """Test bulk write performance for small files."""
        baselines = load_baselines()
        update_baselines = request.config.getoption("--update-baselines")
        skip_regression = request.config.getoption("--skip-regression")

        output_file = tmp_path / "output.csv"
        data = [{"id": i, "name": f"Name{i}", "value": i * 10} for i in range(100)]

        def bulk_write_operation():
            with open_iterable(output_file, "w") as dest:
                dest.write_bulk(data)

        elapsed = measure_operation(bulk_write_operation)

        baseline_key = "bulk_write_small"
        baseline = baselines.get(baseline_key)

        if update_baselines:
            baselines[baseline_key] = elapsed
            save_baselines(baselines)
            pytest.skip("Baseline updated")

        if skip_regression or baseline is None:
            pytest.skip("No baseline available or regression check skipped")

        threshold = PERFORMANCE_THRESHOLDS.get(baseline_key, 1.15)
        max_acceptable = baseline * threshold

        assert elapsed <= max_acceptable, (
            f"Bulk write performance regressed: {elapsed:.4f}s > {max_acceptable:.4f}s "
            f"(baseline: {baseline:.4f}s, threshold: {threshold}x)"
        )


class TestFactoryMethodPerformanceRegression:
    """Test factory method performance regression."""

    def test_factory_method_init_performance(self, tmp_path, request):
        """Test factory method initialization performance."""
        baselines = load_baselines()
        update_baselines = request.config.getoption("--update-baselines")
        skip_regression = request.config.getoption("--skip-regression")

        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test\n")

        # Measure factory method initialization
        elapsed = measure_operation(lambda: CSVIterable.from_file(str(test_file)))

        baseline_key = "factory_method_init"
        baseline = baselines.get(baseline_key)

        if update_baselines:
            baselines[baseline_key] = elapsed
            save_baselines(baselines)
            pytest.skip("Baseline updated")

        if skip_regression or baseline is None:
            pytest.skip("No baseline available or regression check skipped")

        threshold = PERFORMANCE_THRESHOLDS.get(baseline_key, 1.1)
        max_acceptable = baseline * threshold

        assert elapsed <= max_acceptable, (
            f"Factory method init performance regressed: {elapsed:.4f}s > {max_acceptable:.4f}s "
            f"(baseline: {baseline:.4f}s, threshold: {threshold}x)"
        )


class TestFormatDetectionPerformanceRegression:
    """Test format detection performance regression."""

    def test_format_detection_performance(self, small_csv_data, request):
        """Test format detection performance."""
        baselines = load_baselines()
        update_baselines = request.config.getoption("--update-baselines")
        skip_regression = request.config.getoption("--skip-regression")

        elapsed = measure_operation(lambda: open_iterable(small_csv_data))

        baseline_key = "format_detection"
        baseline = baselines.get(baseline_key)

        if update_baselines:
            baselines[baseline_key] = elapsed
            save_baselines(baselines)
            pytest.skip("Baseline updated")

        if skip_regression or baseline is None:
            pytest.skip("No baseline available or regression check skipped")

        threshold = PERFORMANCE_THRESHOLDS.get(baseline_key, 1.2)
        max_acceptable = baseline * threshold

        assert elapsed <= max_acceptable, (
            f"Format detection performance regressed: {elapsed:.4f}s > {max_acceptable:.4f}s "
            f"(baseline: {baseline:.4f}s, threshold: {threshold}x)"
        )


class TestStreamingPerformanceRegression:
    """Test streaming operations performance regression."""

    def test_streaming_read_performance(self, medium_csv_data, request):
        """Test streaming read performance."""
        baselines = load_baselines()
        update_baselines = request.config.getoption("--update-baselines")
        skip_regression = request.config.getoption("--skip-regression")

        # Measure streaming read (iterator, not loading all into memory)
        def streaming_read_operation():
            with open_iterable(medium_csv_data) as source:
                count = 0
                for _row in source:
                    count += 1
                    if count >= 1000:  # Read first 1000 rows
                        break

        elapsed = measure_operation(streaming_read_operation)

        baseline_key = "streaming_read"
        baseline = baselines.get(baseline_key)

        if update_baselines:
            baselines[baseline_key] = elapsed
            save_baselines(baselines)
            pytest.skip("Baseline updated")

        if skip_regression or baseline is None:
            pytest.skip("No baseline available or regression check skipped")

        threshold = PERFORMANCE_THRESHOLDS.get(baseline_key, 1.2)
        max_acceptable = baseline * threshold

        assert elapsed <= max_acceptable, (
            f"Streaming read performance regressed: {elapsed:.4f}s > {max_acceptable:.4f}s "
            f"(baseline: {baseline:.4f}s, threshold: {threshold}x)"
        )


class TestResetPerformanceRegression:
    """Test reset operation performance regression."""

    def test_reset_operation_performance(self, small_csv_data, request):
        """Test reset operation performance."""
        baselines = load_baselines()
        update_baselines = request.config.getoption("--update-baselines")
        skip_regression = request.config.getoption("--skip-regression")

        def reset_operation():
            with open_iterable(small_csv_data) as source:
                source.read()  # Read one row
                source.reset()  # Reset
                source.read()  # Read again

        elapsed = measure_operation(reset_operation)

        baseline_key = "reset_operation"
        baseline = baselines.get(baseline_key)

        if update_baselines:
            baselines[baseline_key] = elapsed
            save_baselines(baselines)
            pytest.skip("Baseline updated")

        if skip_regression or baseline is None:
            pytest.skip("No baseline available or regression check skipped")

        threshold = PERFORMANCE_THRESHOLDS.get(baseline_key, 1.2)
        max_acceptable = baseline * threshold

        assert elapsed <= max_acceptable, (
            f"Reset operation performance regressed: {elapsed:.4f}s > {max_acceptable:.4f}s "
            f"(baseline: {baseline:.4f}s, threshold: {threshold}x)"
        )
