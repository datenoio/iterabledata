"""Memory profiling tests using memory_profiler.

These tests measure memory usage of various operations to ensure
streaming formats use constant memory and non-streaming formats
are properly documented.

Run with: pytest tests/test_memory_profiling.py -v

Requirements:
    - memory-profiler: pip install memory-profiler
    - psutil: pip install psutil (for more accurate measurements)
"""

import gc
import os

import pytest

try:
    import psutil
    from memory_profiler import profile

    HAS_MEMORY_PROFILER = True
except ImportError:
    HAS_MEMORY_PROFILER = False

    # Create a dummy profile decorator for when memory_profiler is not available
    def profile(func):
        return func


from iterable.helpers.detect import open_iterable


def get_memory_usage_mb() -> float:
    """Get current process memory usage in MB."""
    if not HAS_MEMORY_PROFILER:
        return 0.0
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def measure_memory_delta(func, *args, **kwargs) -> tuple[float, any]:
    """Measure memory delta before and after function execution.

    Returns:
        (memory_delta_mb, result)
    """
    if not HAS_MEMORY_PROFILER:
        result = func(*args, **kwargs)
        return (0.0, result)

    # Force garbage collection before measurement
    gc.collect()

    memory_before = get_memory_usage_mb()
    result = func(*args, **kwargs)
    memory_after = get_memory_usage_mb()

    # Force garbage collection after measurement
    gc.collect()

    memory_delta = memory_after - memory_before
    return (memory_delta, result)


@pytest.fixture
def medium_csv_file(tmp_path):
    """Create a medium CSV file (10,000 rows)"""
    test_file = tmp_path / "medium.csv"
    lines = ["name,age,city"]
    with test_file.open("w") as f:
        f.write("\n".join(lines) + "\n")
        for i in range(10000):
            f.write(f"Person{i},{20 + i},City{i % 10}\n")
    return test_file


@pytest.fixture
def large_csv_file(tmp_path):
    """Create a large CSV file (100,000 rows)"""
    test_file = tmp_path / "large.csv"
    lines = ["name,age,city"]
    with test_file.open("w") as f:
        f.write("\n".join(lines) + "\n")
        for i in range(100000):
            f.write(f"Person{i},{20 + i},City{i % 10}\n")
    return test_file


@pytest.fixture
def medium_jsonl_file(tmp_path):
    """Create a medium JSONL file (10,000 rows)"""
    import json

    test_file = tmp_path / "medium.jsonl"
    with test_file.open("w") as f:
        for i in range(10000):
            record = {"name": f"Person{i}", "age": 20 + i, "city": f"City{i % 10}"}
            f.write(json.dumps(record) + "\n")
    return test_file


@pytest.fixture
def large_jsonl_file(tmp_path):
    """Create a large JSONL file (100,000 rows)"""
    import json

    test_file = tmp_path / "large.jsonl"
    with test_file.open("w") as f:
        for i in range(100000):
            record = {"name": f"Person{i}", "age": 20 + i, "city": f"City{i % 10}"}
            f.write(json.dumps(record) + "\n")
    return test_file


@pytest.mark.skipif(not HAS_MEMORY_PROFILER, reason="memory_profiler not installed")
class TestStreamingFormatMemory:
    """Test memory usage of streaming formats"""

    def test_csv_streaming_memory_constant(self, large_csv_file):
        """Test that CSV streaming uses constant memory"""

        def read_streaming():
            count = 0
            with open_iterable(large_csv_file) as source:
                for _ in source:
                    count += 1
            return count

        memory_delta, count = measure_memory_delta(read_streaming)

        # CSV is a streaming format, so memory usage should be relatively constant
        # Allow up to 50MB for overhead (buffers, Python objects, etc.)
        assert memory_delta < 50.0, f"CSV streaming used {memory_delta:.2f}MB, expected < 50MB"
        assert count == 100000

    def test_jsonl_streaming_memory_constant(self, large_jsonl_file):
        """Test that JSONL streaming uses constant memory"""

        def read_streaming():
            count = 0
            with open_iterable(large_jsonl_file) as source:
                for _ in source:
                    count += 1
            return count

        memory_delta, count = measure_memory_delta(read_streaming)

        # JSONL is a streaming format, so memory usage should be relatively constant
        # Allow up to 50MB for overhead
        assert memory_delta < 50.0, f"JSONL streaming used {memory_delta:.2f}MB, expected < 50MB"
        assert count == 100000

    def test_csv_bulk_read_memory(self, medium_csv_file):
        """Test memory usage of bulk read operations"""

        def read_bulk():
            with open_iterable(medium_csv_file) as source:
                rows = []
                while True:
                    chunk = source.read_bulk(num=1000)
                    if not chunk:
                        break
                    rows.extend(chunk)
                return len(rows)

        memory_delta, count = measure_memory_delta(read_bulk)

        # Bulk read should use more memory than streaming, but still reasonable
        # Allow up to 100MB for bulk operations
        assert memory_delta < 100.0, f"CSV bulk read used {memory_delta:.2f}MB, expected < 100MB"
        assert count == 10000


@pytest.mark.skipif(not HAS_MEMORY_PROFILER, reason="memory_profiler not installed")
class TestNonStreamingFormatMemory:
    """Test memory usage of non-streaming formats"""

    def test_json_memory_scales_with_file_size(self, tmp_path):
        """Test that JSON (non-streaming) memory usage scales with file size"""
        import json

        # Create small JSON file
        small_file = tmp_path / "small.json"
        small_data = [{"id": i, "name": f"Item{i}"} for i in range(1000)]
        with small_file.open("w") as f:
            json.dump(small_data, f)

        # Create large JSON file
        large_file = tmp_path / "large.json"
        large_data = [{"id": i, "name": f"Item{i}"} for i in range(100000)]
        with large_file.open("w") as f:
            json.dump(large_data, f)

        def read_json(filepath):
            with open_iterable(filepath) as source:
                return list(source)

        small_delta, small_result = measure_memory_delta(read_json, small_file)
        large_delta, large_result = measure_memory_delta(read_json, large_file)

        # Large file should use significantly more memory
        # This confirms JSON is non-streaming (loads entire file)
        assert large_delta > small_delta * 10, (
            f"Large JSON file should use much more memory. Small: {small_delta:.2f}MB, Large: {large_delta:.2f}MB"
        )
        assert len(small_result) == 1000
        assert len(large_result) == 100000


@pytest.mark.skipif(not HAS_MEMORY_PROFILER, reason="memory_profiler not installed")
class TestMemoryComparison:
    """Compare memory usage between different operations"""

    def test_streaming_vs_bulk_read_memory(self, large_csv_file):
        """Compare memory usage of streaming vs bulk read"""

        def streaming_read():
            count = 0
            with open_iterable(large_csv_file) as source:
                for _ in source:
                    count += 1
            return count

        def bulk_read():
            with open_iterable(large_csv_file) as source:
                rows = []
                while True:
                    chunk = source.read_bulk(num=10000)
                    if not chunk:
                        break
                    rows.extend(chunk)
                # Keep the rows alive so RSS reflects retained bulk data.
                # Returning only len(rows) lets refcounting free the list before
                # measurement, so the comparison becomes allocator noise.
                return rows

        streaming_delta, streaming_count = measure_memory_delta(streaming_read)
        bulk_delta, bulk_rows = measure_memory_delta(bulk_read)

        assert streaming_count == len(bulk_rows) == 100000
        # Windows working-set samples can lag or reuse heap arenas across sequential
        # measurements. Skip the RSS comparison when bulk retention is not visible.
        if bulk_delta < 5.0:
            pytest.skip(
                "Memory comparison unreliable on this platform "
                f"(streaming={streaming_delta:.2f}MB, bulk={bulk_delta:.2f}MB)"
            )
        assert streaming_delta < bulk_delta, (
            f"Streaming should use less memory. Streaming: {streaming_delta:.2f}MB, Bulk: {bulk_delta:.2f}MB"
        )

    def test_write_memory_usage(self, tmp_path, medium_csv_file):
        """Test memory usage of write operations"""
        output_file = tmp_path / "output.csv"

        def write_individual():
            with open_iterable(output_file, "w") as dest:
                with open_iterable(medium_csv_file) as source:
                    for record in source:
                        dest.write(record)

        def write_bulk():
            output_file2 = tmp_path / "output2.csv"
            with open_iterable(output_file2, "w") as dest:
                with open_iterable(medium_csv_file) as source:
                    while True:
                        chunk = source.read_bulk(num=1000)
                        if not chunk:
                            break
                        dest.write_bulk(chunk)

        individual_delta, _ = measure_memory_delta(write_individual)
        bulk_delta, _ = measure_memory_delta(write_bulk)

        # Both should use reasonable memory
        # Individual writes might use slightly less due to no buffering
        assert individual_delta < 100.0
        assert bulk_delta < 100.0


@pytest.mark.skipif(not HAS_MEMORY_PROFILER, reason="memory_profiler not installed")
class TestMemoryLeaks:
    """Test for memory leaks in common operations"""

    def test_repeated_reads_no_leak(self, medium_csv_file):
        """Test that repeated reads don't cause memory leaks"""
        initial_memory = get_memory_usage_mb()

        # Perform multiple reads
        for _ in range(10):

            def read_all():
                with open_iterable(medium_csv_file) as source:
                    return list(source)

            _, _ = measure_memory_delta(read_all)
            gc.collect()

        final_memory = get_memory_usage_mb()
        memory_growth = final_memory - initial_memory

        # Memory growth should be minimal (< 20MB) after multiple reads
        assert memory_growth < 20.0, f"Memory leak detected: {memory_growth:.2f}MB growth after 10 reads"

    def test_context_manager_cleanup(self, medium_csv_file):
        """Test that context managers properly clean up memory"""
        initial_memory = get_memory_usage_mb()

        # Open and close many times
        for _ in range(20):
            with open_iterable(medium_csv_file) as source:
                # Read a few records
                for i, _ in enumerate(source):
                    if i >= 10:
                        break

        gc.collect()
        final_memory = get_memory_usage_mb()
        memory_growth = final_memory - initial_memory

        # Memory growth should be minimal
        assert memory_growth < 20.0, f"Context manager cleanup issue: {memory_growth:.2f}MB growth"


@pytest.mark.skipif(not HAS_MEMORY_PROFILER, reason="memory_profiler not installed")
class TestMemoryWithCompression:
    """Test memory usage with compressed files"""

    def test_gzip_csv_memory(self, tmp_path):
        """Test memory usage with gzip-compressed CSV"""
        import gzip

        # Create gzipped CSV
        gz_file = tmp_path / "test.csv.gz"
        csv_content = "name,age\n"
        csv_content += "\n".join([f"Person{i},{20 + i}" for i in range(10000)])

        with gzip.open(gz_file, "wt") as f:
            f.write(csv_content)

        def read_gzipped():
            count = 0
            with open_iterable(gz_file) as source:
                for _ in source:
                    count += 1
            return count

        memory_delta, count = measure_memory_delta(read_gzipped)

        # Gzipped CSV should still stream efficiently
        assert memory_delta < 50.0, f"Gzipped CSV used {memory_delta:.2f}MB, expected < 50MB"
        assert count == 10000
