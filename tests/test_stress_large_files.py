"""Stress tests for very large files (10GB+).

These tests verify that IterableData can handle very large files
without running out of memory or encountering errors.

WARNING: These tests create large files (10GB+) and may take a long time to run.
They are marked with @pytest.mark.stress and can be skipped with:
    pytest -m "not stress"

To run stress tests:
    pytest tests/test_stress_large_files.py -m stress -v

Requirements:
    - Sufficient disk space (10GB+)
    - Sufficient time (tests may take 30+ minutes)
"""

import time
from pathlib import Path

import pytest

from iterable.helpers.detect import open_iterable


def create_large_csv_file(filepath: Path, target_size_gb: float = 1.0, chunk_size_mb: int = 100) -> None:
    """Create a large CSV file by writing in chunks.

    Args:
        filepath: Path to create file at
        target_size_gb: Target file size in GB
        chunk_size_mb: Size of each write chunk in MB
    """
    target_size_bytes = int(target_size_gb * 1024 * 1024 * 1024)
    chunk_size_bytes = chunk_size_mb * 1024 * 1024

    header = "id,name,age,city,value1,value2,value3,value4,value5\n"
    row_template = "{id},Person{id},{age},City{city_id},{val1},{val2},{val3},{val4},{val5}\n"

    with filepath.open("w") as f:
        f.write(header)
        written = len(header.encode("utf-8"))
        row_id = 0

        while written < target_size_bytes:
            # Generate chunk of rows
            chunk_rows = []
            chunk_size = 0

            while chunk_size < chunk_size_bytes and written + chunk_size < target_size_bytes:
                row = row_template.format(
                    id=row_id,
                    age=20 + (row_id % 100),
                    city_id=row_id % 10,
                    val1=row_id * 1.1,
                    val2=row_id * 2.2,
                    val3=row_id * 3.3,
                    val4=row_id * 4.4,
                    val5=row_id * 5.5,
                )
                chunk_rows.append(row)
                chunk_size += len(row.encode("utf-8"))
                row_id += 1

            # Write chunk
            f.write("".join(chunk_rows))
            written += chunk_size

            # Progress indicator
            if row_id % 100000 == 0:
                size_mb = written / (1024 * 1024)
                print(f"  Created {size_mb:.1f} MB, {row_id} rows...")


def create_large_jsonl_file(filepath: Path, target_size_gb: float = 1.0, chunk_size_mb: int = 100) -> None:
    """Create a large JSONL file by writing in chunks.

    Args:
        filepath: Path to create file at
        target_size_gb: Target file size in GB
        chunk_size_mb: Size of each write chunk in MB
    """
    import json

    target_size_bytes = int(target_size_gb * 1024 * 1024 * 1024)
    chunk_size_bytes = chunk_size_mb * 1024 * 1024

    with filepath.open("w") as f:
        written = 0
        row_id = 0

        while written < target_size_bytes:
            # Generate chunk of rows
            chunk_rows = []
            chunk_size = 0

            while chunk_size < chunk_size_bytes and written + chunk_size < target_size_bytes:
                record = {
                    "id": row_id,
                    "name": f"Person{row_id}",
                    "age": 20 + (row_id % 100),
                    "city": f"City{row_id % 10}",
                    "value1": row_id * 1.1,
                    "value2": row_id * 2.2,
                    "value3": row_id * 3.3,
                    "value4": row_id * 4.4,
                    "value5": row_id * 5.5,
                }
                row = json.dumps(record) + "\n"
                chunk_rows.append(row)
                chunk_size += len(row.encode("utf-8"))
                row_id += 1

            # Write chunk
            f.write("".join(chunk_rows))
            written += chunk_size

            # Progress indicator
            if row_id % 100000 == 0:
                size_mb = written / (1024 * 1024)
                print(f"  Created {size_mb:.1f} MB, {row_id} rows...")


@pytest.fixture(scope="session")
def large_csv_1gb(tmp_path_factory):
    """Create a 1GB CSV file (session-scoped to reuse across tests)"""
    tmp_path = tmp_path_factory.mktemp("stress_large")
    filepath = tmp_path / "large_1gb.csv"

    if not filepath.exists():
        print(f"Creating 1GB CSV file at {filepath}...")
        start_time = time.time()
        create_large_csv_file(filepath, target_size_gb=1.0)
        elapsed = time.time() - start_time
        print(f"Created 1GB CSV file in {elapsed:.1f} seconds")

    yield filepath

    # Cleanup (optional - comment out to keep files for debugging)
    # if filepath.exists():
    #     filepath.unlink()


@pytest.fixture(scope="session")
def large_csv_10gb(tmp_path_factory):
    """Create a 10GB CSV file (session-scoped to reuse across tests)"""
    tmp_path = tmp_path_factory.mktemp("stress_large")
    filepath = tmp_path / "large_10gb.csv"

    if not filepath.exists():
        print(f"Creating 10GB CSV file at {filepath}...")
        print("WARNING: This may take 10-30 minutes depending on disk speed...")
        start_time = time.time()
        create_large_csv_file(filepath, target_size_gb=10.0)
        elapsed = time.time() - start_time
        print(f"Created 10GB CSV file in {elapsed:.1f} seconds ({elapsed / 60:.1f} minutes)")

    yield filepath

    # Cleanup (optional - comment out to keep files for debugging)
    # if filepath.exists():
    #     filepath.unlink()


@pytest.fixture(scope="session")
def large_jsonl_1gb(tmp_path_factory):
    """Create a 1GB JSONL file (session-scoped to reuse across tests)"""
    tmp_path = tmp_path_factory.mktemp("stress_large")
    filepath = tmp_path / "large_1gb.jsonl"

    if not filepath.exists():
        print(f"Creating 1GB JSONL file at {filepath}...")
        start_time = time.time()
        create_large_jsonl_file(filepath, target_size_gb=1.0)
        elapsed = time.time() - start_time
        print(f"Created 1GB JSONL file in {elapsed:.1f} seconds")

    yield filepath


@pytest.fixture(scope="session")
def large_jsonl_10gb(tmp_path_factory):
    """Create a 10GB JSONL file (session-scoped to reuse across tests)"""
    tmp_path = tmp_path_factory.mktemp("stress_large")
    filepath = tmp_path / "large_10gb.jsonl"

    if not filepath.exists():
        print(f"Creating 10GB JSONL file at {filepath}...")
        print("WARNING: This may take 10-30 minutes depending on disk speed...")
        start_time = time.time()
        create_large_jsonl_file(filepath, target_size_gb=10.0)
        elapsed = time.time() - start_time
        print(f"Created 10GB JSONL file in {elapsed:.1f} seconds ({elapsed / 60:.1f} minutes)")

    yield filepath


@pytest.mark.stress
class TestLargeFileStreaming:
    """Test streaming operations on very large files"""

    def test_csv_1gb_streaming_read(self, large_csv_1gb):
        """Test streaming read of 1GB CSV file"""
        count = 0
        start_time = time.time()

        with open_iterable(large_csv_1gb) as source:
            for row in source:
                count += 1
                # Verify row structure
                assert "id" in row or "name" in row
                # Progress indicator for very large files
                if count % 1000000 == 0:
                    elapsed = time.time() - start_time
                    print(f"  Read {count} rows in {elapsed:.1f} seconds...")

        elapsed = time.time() - start_time
        print(f"Read {count} rows from 1GB CSV in {elapsed:.1f} seconds")
        assert count > 0

    @pytest.mark.slow
    def test_csv_10gb_streaming_read(self, large_csv_10gb):
        """Test streaming read of 10GB CSV file"""
        count = 0
        start_time = time.time()

        with open_iterable(large_csv_10gb) as source:
            for row in source:
                count += 1
                # Verify row structure
                assert "id" in row or "name" in row
                # Progress indicator
                if count % 1000000 == 0:
                    elapsed = time.time() - start_time
                    rate = count / elapsed if elapsed > 0 else 0
                    print(f"  Read {count} rows in {elapsed:.1f} seconds ({rate:.0f} rows/sec)...")

        elapsed = time.time() - start_time
        print(f"Read {count} rows from 10GB CSV in {elapsed:.1f} seconds ({elapsed / 60:.1f} minutes)")
        assert count > 0

    def test_jsonl_1gb_streaming_read(self, large_jsonl_1gb):
        """Test streaming read of 1GB JSONL file"""
        count = 0
        start_time = time.time()

        with open_iterable(large_jsonl_1gb) as source:
            for row in source:
                count += 1
                # Verify row structure
                assert "id" in row
                if count % 1000000 == 0:
                    elapsed = time.time() - start_time
                    print(f"  Read {count} rows in {elapsed:.1f} seconds...")

        elapsed = time.time() - start_time
        print(f"Read {count} rows from 1GB JSONL in {elapsed:.1f} seconds")
        assert count > 0

    @pytest.mark.slow
    def test_jsonl_10gb_streaming_read(self, large_jsonl_10gb):
        """Test streaming read of 10GB JSONL file"""
        count = 0
        start_time = time.time()

        with open_iterable(large_jsonl_10gb) as source:
            for row in source:
                count += 1
                # Verify row structure
                assert "id" in row
                if count % 1000000 == 0:
                    elapsed = time.time() - start_time
                    rate = count / elapsed if elapsed > 0 else 0
                    print(f"  Read {count} rows in {elapsed:.1f} seconds ({rate:.0f} rows/sec)...")

        elapsed = time.time() - start_time
        print(f"Read {count} rows from 10GB JSONL in {elapsed:.1f} seconds ({elapsed / 60:.1f} minutes)")
        assert count > 0


@pytest.mark.stress
class TestLargeFileBulkOperations:
    """Test bulk operations on very large files"""

    def test_csv_1gb_bulk_read(self, large_csv_1gb):
        """Test bulk read of 1GB CSV file"""
        total_count = 0
        chunk_count = 0
        start_time = time.time()

        with open_iterable(large_csv_1gb) as source:
            for chunk in source.read_bulk(num=100000):
                chunk_count += 1
                total_count += len(chunk)
                # Verify chunk structure
                assert len(chunk) > 0
                assert isinstance(chunk[0], dict)
                if chunk_count % 10 == 0:
                    elapsed = time.time() - start_time
                    print(f"  Read {chunk_count} chunks, {total_count} rows in {elapsed:.1f} seconds...")

        elapsed = time.time() - start_time
        print(f"Read {total_count} rows in {chunk_count} chunks from 1GB CSV in {elapsed:.1f} seconds")
        assert total_count > 0

    @pytest.mark.slow
    def test_csv_10gb_bulk_read(self, large_csv_10gb):
        """Test bulk read of 10GB CSV file"""
        total_count = 0
        chunk_count = 0
        start_time = time.time()

        with open_iterable(large_csv_10gb) as source:
            for chunk in source.read_bulk(num=100000):
                chunk_count += 1
                total_count += len(chunk)
                if chunk_count % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = total_count / elapsed if elapsed > 0 else 0
                    print(
                        f"  Read {chunk_count} chunks, {total_count} rows in "
                        f"{elapsed:.1f} seconds ({rate:.0f} rows/sec)..."
                    )

        elapsed = time.time() - start_time
        print(
            f"Read {total_count} rows in {chunk_count} chunks from 10GB CSV in "
            f"{elapsed:.1f} seconds ({elapsed / 60:.1f} minutes)"
        )
        assert total_count > 0


@pytest.mark.stress
class TestLargeFileOperations:
    """Test various operations on very large files"""

    def test_csv_1gb_reset(self, large_csv_1gb):
        """Test reset operation on 1GB CSV file"""
        with open_iterable(large_csv_1gb) as source:
            # Read first 100 rows
            first_rows = []
            for i, row in enumerate(source):
                first_rows.append(row)
                if i >= 99:
                    break

            # Reset and read again
            source.reset()

            # Verify we can read the same rows again
            for i, row in enumerate(source):
                if i >= 99:
                    break
                assert row == first_rows[i]

    def test_csv_1gb_partial_read(self, large_csv_1gb):
        """Test reading only part of a large file"""
        count = 0
        with open_iterable(large_csv_1gb) as source:
            # Read only first 1000 rows
            for _row in source:
                count += 1
                if count >= 1000:
                    break

        assert count == 1000

    def test_csv_1gb_seek_operations(self, large_csv_1gb):
        """Test that seek operations work on large files"""
        with open_iterable(large_csv_1gb) as source:
            # Read some rows
            rows1 = []
            for i, row in enumerate(source):
                rows1.append(row)
                if i >= 9:
                    break

            # Reset and read again
            source.reset()
            rows2 = []
            for i, row in enumerate(source):
                rows2.append(row)
                if i >= 9:
                    break

            # Should get same rows
            assert rows1 == rows2


@pytest.mark.stress
class TestLargeFileMemory:
    """Test memory usage with very large files"""

    def test_csv_1gb_memory_constant(self, large_csv_1gb):
        """Test that reading 1GB CSV uses constant memory"""
        try:
            import os

            import psutil

            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024  # MB

            count = 0
            with open_iterable(large_csv_1gb) as source:
                for _row in source:
                    count += 1
                    # Check memory every 100k rows
                    if count % 100000 == 0:
                        memory_current = process.memory_info().rss / 1024 / 1024
                        memory_delta = memory_current - memory_before
                        # Memory should stay relatively constant (< 200MB growth)
                        assert memory_delta < 200, (
                            f"Memory usage grew too much: {memory_delta:.1f}MB after {count} rows"
                        )

            memory_after = process.memory_info().rss / 1024 / 1024
            memory_total = memory_after - memory_before
            print(f"Total memory used: {memory_total:.1f}MB for {count} rows")
            assert memory_total < 200, f"Total memory usage too high: {memory_total:.1f}MB"

        except ImportError:
            pytest.skip("psutil not available for memory testing")


@pytest.mark.stress
class TestLargeFileErrorHandling:
    """Test error handling with very large files"""

    def test_csv_1gb_error_recovery(self, large_csv_1gb):
        """Test that errors don't cause memory leaks or hangs"""
        error_count = 0
        success_count = 0

        with open_iterable(large_csv_1gb, options={"on_error": "skip"}) as source:
            for row in source:
                try:
                    # Simulate processing that might fail
                    if "invalid" in str(row).lower():
                        error_count += 1
                    else:
                        success_count += 1

                    # Stop after reasonable number of rows for test
                    if success_count >= 10000:
                        break
                except Exception:
                    error_count += 1

        assert success_count > 0
        print(f"Processed {success_count} rows successfully, {error_count} errors")


@pytest.mark.stress
@pytest.mark.slow
class TestLargeFileConversion:
    """Test format conversion with very large files"""

    def test_csv_1gb_to_jsonl(self, large_csv_1gb, tmp_path):
        """Test converting 1GB CSV to JSONL"""
        from iterable.convert import convert

        output_file = tmp_path / "output.jsonl"

        start_time = time.time()
        convert(
            fromfile=str(large_csv_1gb),
            tofile=str(output_file),
            batch_size=100000,
        )
        elapsed = time.time() - start_time

        # Verify output file exists and has reasonable size
        assert output_file.exists()
        output_size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"Converted 1GB CSV to JSONL in {elapsed:.1f} seconds, output: {output_size_mb:.1f} MB")

        # Verify we can read the output
        count = 0
        with open_iterable(output_file) as source:
            for _row in source:
                count += 1
                if count >= 1000:
                    break

        assert count > 0
