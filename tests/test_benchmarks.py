"""Performance benchmarks using pytest-benchmark.

These benchmarks measure the performance of various operations in IterableData.
Run with: pytest tests/test_benchmarks.py --benchmark-only

To compare with previous runs:
    pytest tests/test_benchmarks.py --benchmark-only --benchmark-compare
"""

import pytest

pytest.importorskip("pytest_benchmark", reason="pytest-benchmark not installed (pip install pytest-benchmark)")

from iterable.datatypes.csv import CSVIterable  # noqa: E402
from iterable.helpers.detect import open_iterable  # noqa: E402

# Excluded from the default run via addopts; run with: pytest -m benchmark
pytestmark = pytest.mark.benchmark


@pytest.fixture
def small_csv_data(tmp_path):
    """Create a small CSV file for testing"""
    test_file = tmp_path / "small.csv"
    # Create CSV with 100 rows
    lines = ["name,age,city"] + [f"Person{i},{20 + i},City{i % 10}" for i in range(100)]
    test_file.write_text("\n".join(lines))
    return test_file


@pytest.fixture
def medium_csv_data(tmp_path):
    """Create a medium CSV file for testing"""
    test_file = tmp_path / "medium.csv"
    # Create CSV with 10,000 rows
    lines = ["name,age,city"] + [f"Person{i},{20 + i},City{i % 10}" for i in range(10000)]
    test_file.write_text("\n".join(lines))
    return test_file


@pytest.fixture
def large_csv_data(tmp_path):
    """Create a large CSV file for testing"""
    test_file = tmp_path / "large.csv"
    # Create CSV with 100,000 rows
    lines = ["name,age,city"]
    # Write in chunks to avoid memory issues
    with test_file.open("w") as f:
        f.write("\n".join(lines) + "\n")
        for i in range(100000):
            f.write(f"Person{i},{20 + i},City{i % 10}\n")
    return test_file


@pytest.fixture
def small_jsonl_data(tmp_path):
    """Create a small JSONL file for testing"""
    test_file = tmp_path / "small.jsonl"
    lines = [f'{{"name":"Person{i}","age":{20 + i},"city":"City{i % 10}"}}' for i in range(100)]
    test_file.write_text("\n".join(lines))
    return test_file


@pytest.fixture
def medium_jsonl_data(tmp_path):
    """Create a medium JSONL file for testing"""
    test_file = tmp_path / "medium.jsonl"
    lines = [f'{{"name":"Person{i}","age":{20 + i},"city":"City{i % 10}"}}' for i in range(10000)]
    test_file.write_text("\n".join(lines))
    return test_file


class TestCSVBenchmarks:
    """Benchmark CSV operations"""

    def test_csv_read_small(self, benchmark, small_csv_data):
        """Benchmark reading small CSV file"""

        def read_all():
            with open_iterable(small_csv_data) as source:
                return list(source)

        result = benchmark(read_all)
        assert len(result) == 100

    def test_csv_read_medium(self, benchmark, medium_csv_data):
        """Benchmark reading medium CSV file"""

        def read_all():
            with open_iterable(medium_csv_data) as source:
                return list(source)

        result = benchmark(read_all)
        assert len(result) == 10000

    def test_csv_read_large(self, benchmark, large_csv_data):
        """Benchmark reading large CSV file"""

        def read_all():
            with open_iterable(large_csv_data) as source:
                return list(source)

        result = benchmark(read_all)
        assert len(result) == 100000

    def test_csv_read_bulk_small(self, benchmark, small_csv_data):
        """Benchmark read_bulk on small CSV file"""

        def read_bulk():
            with open_iterable(small_csv_data) as source:
                chunks = []
                while batch := source.read_bulk(num=10):
                    chunks.extend(batch)
                return chunks

        result = benchmark(read_bulk)
        assert len(result) == 100

    def test_csv_read_bulk_medium(self, benchmark, medium_csv_data):
        """Benchmark read_bulk on medium CSV file"""

        def read_bulk():
            with open_iterable(medium_csv_data) as source:
                chunks = []
                while batch := source.read_bulk(num=1000):
                    chunks.extend(batch)
                return chunks

        result = benchmark(read_bulk)
        assert len(result) == 10000

    def test_csv_write_small(self, benchmark, tmp_path):
        """Benchmark writing small CSV file"""
        output_file = tmp_path / "output.csv"
        data = [{"name": f"Person{i}", "age": 20 + i, "city": f"City{i % 10}"} for i in range(100)]

        def write_all():
            with open_iterable(output_file, "w") as dest:
                dest.write_bulk(data)

        benchmark(write_all)
        assert output_file.exists()

    def test_csv_write_medium(self, benchmark, tmp_path):
        """Benchmark writing medium CSV file"""
        output_file = tmp_path / "output.csv"
        data = [{"name": f"Person{i}", "age": 20 + i, "city": f"City{i % 10}"} for i in range(10000)]

        def write_all():
            with open_iterable(output_file, "w") as dest:
                dest.write_bulk(data)

        benchmark(write_all)
        assert output_file.exists()


class TestJSONLBenchmarks:
    """Benchmark JSONL operations"""

    def test_jsonl_read_small(self, benchmark, small_jsonl_data):
        """Benchmark reading small JSONL file"""

        def read_all():
            with open_iterable(small_jsonl_data) as source:
                return list(source)

        result = benchmark(read_all)
        assert len(result) == 100

    def test_jsonl_read_medium(self, benchmark, medium_jsonl_data):
        """Benchmark reading medium JSONL file"""

        def read_all():
            with open_iterable(medium_jsonl_data) as source:
                return list(source)

        result = benchmark(read_all)
        assert len(result) == 10000

    def test_jsonl_read_bulk_small(self, benchmark, small_jsonl_data):
        """Benchmark read_bulk on small JSONL file"""

        def read_bulk():
            with open_iterable(small_jsonl_data) as source:
                chunks = []
                while batch := source.read_bulk(num=10):
                    chunks.extend(batch)
                return chunks

        result = benchmark(read_bulk)
        assert len(result) == 100

    def test_jsonl_write_small(self, benchmark, tmp_path):
        """Benchmark writing small JSONL file"""
        output_file = tmp_path / "output.jsonl"
        data = [{"name": f"Person{i}", "age": 20 + i, "city": f"City{i % 10}"} for i in range(100)]

        def write_all():
            with open_iterable(output_file, "w") as dest:
                dest.write_bulk(data)

        benchmark(write_all)
        assert output_file.exists()


class TestFormatDetectionBenchmarks:
    """Benchmark format detection operations"""

    def test_detect_csv(self, benchmark, small_csv_data):
        """Benchmark CSV format detection"""

        def detect():
            return open_iterable(small_csv_data)

        result = benchmark.pedantic(detect, iterations=10, rounds=100)
        assert result is not None

    def test_detect_jsonl(self, benchmark, small_jsonl_data):
        """Benchmark JSONL format detection"""

        def detect():
            return open_iterable(small_jsonl_data)

        result = benchmark.pedantic(detect, iterations=10, rounds=100)
        assert result is not None


class TestStreamingBenchmarks:
    """Benchmark streaming operations"""

    def test_csv_streaming_read(self, benchmark, large_csv_data):
        """Benchmark streaming read (one row at a time)"""

        def stream_read():
            count = 0
            with open_iterable(large_csv_data) as source:
                for _ in source:
                    count += 1
            return count

        result = benchmark(stream_read)
        assert result == 100000

    def test_jsonl_streaming_read(self, benchmark, medium_jsonl_data):
        """Benchmark streaming read (one row at a time)"""

        def stream_read():
            count = 0
            with open_iterable(medium_jsonl_data) as source:
                for _ in source:
                    count += 1
            return count

        result = benchmark(stream_read)
        assert result == 10000


class TestFactoryMethodBenchmarks:
    """Benchmark factory method initialization"""

    def test_from_file_factory(self, benchmark, small_csv_data):
        """Benchmark from_file factory method"""

        def create():
            return CSVIterable.from_file(str(small_csv_data), noopen=True)

        result = benchmark(create)
        assert result is not None

    def test_traditional_init(self, benchmark, small_csv_data):
        """Benchmark traditional __init__ method"""

        def create():
            it = CSVIterable(filename=str(small_csv_data))
            it.close()
            return it

        result = benchmark(create)
        assert result is not None


class TestBulkOperationsBenchmarks:
    """Benchmark bulk operations vs individual operations"""

    def test_bulk_vs_individual_read(self, benchmark, medium_csv_data):
        """Compare bulk read vs individual read performance"""

        def bulk_read():
            with open_iterable(medium_csv_data) as source:
                chunks = []
                while batch := source.read_bulk(num=1000):
                    chunks.extend(batch)
                return chunks

        def individual_read():
            with open_iterable(medium_csv_data) as source:
                return list(source)

        # pytest-benchmark allows a single benchmark() call per test; benchmark
        # the bulk path and verify equivalence with the individual path separately.
        bulk_result = benchmark(bulk_read)
        individual_result = individual_read()

        # Both should return same data
        assert len(bulk_result) == len(individual_result) == 10000

    def test_bulk_vs_individual_write(self, benchmark, tmp_path):
        """Compare bulk write vs individual write performance"""
        data = [{"name": f"Person{i}", "age": 20 + i} for i in range(1000)]

        def bulk_write():
            output = tmp_path / "bulk.csv"
            with open_iterable(output, "w") as dest:
                dest.write_bulk(data)

        def individual_write():
            output = tmp_path / "individual.csv"
            with open_iterable(output, "w") as dest:
                for record in data:
                    dest.write(record)

        # pytest-benchmark allows a single benchmark() call per test; benchmark
        # the bulk path and run the individual path once for comparison coverage.
        benchmark(bulk_write)
        individual_write()

        # Both files should exist
        assert (tmp_path / "bulk.csv").exists()
        assert (tmp_path / "individual.csv").exists()
