"""Concurrent access tests for IterableData.

These tests verify that IterableData can handle concurrent access
from multiple threads or processes safely.

Run with: pytest tests/test_concurrent_access.py -v
"""

import concurrent.futures
import threading

import pytest

from iterable.helpers.detect import open_iterable


@pytest.fixture
def shared_csv_file(tmp_path):
    """Create a CSV file for concurrent reading"""
    test_file = tmp_path / "shared.csv"
    lines = ["id,name,value"]
    lines.extend([f"{i},Person{i},{i * 1.5}" for i in range(10000)])
    test_file.write_text("\n".join(lines))
    return test_file


@pytest.fixture
def multiple_csv_files(tmp_path):
    """Create multiple CSV files for concurrent processing"""
    files = []
    for i in range(5):
        test_file = tmp_path / f"file{i}.csv"
        lines = ["id,name,value"]
        lines.extend([f"{j},Person{j},{j * 1.5}" for j in range(1000)])
        test_file.write_text("\n".join(lines))
        files.append(test_file)
    return files


class TestConcurrentRead:
    """Test concurrent reading from the same file"""

    def test_multiple_threads_read_same_file(self, shared_csv_file):
        """Test multiple threads reading from the same file"""
        results = []
        errors = []

        def read_file(thread_id):
            try:
                count = 0
                with open_iterable(shared_csv_file) as source:
                    for row in source:
                        count += 1
                        # Verify row structure
                        assert "id" in row or "name" in row
                results.append((thread_id, count))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create 5 threads reading the same file
        threads = []
        for i in range(5):
            thread = threading.Thread(target=read_file, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)

        # Verify all threads completed successfully
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"

        # All threads should read the same number of rows
        counts = [count for _, count in results]
        assert all(count == counts[0] for count in counts), "Threads read different numbers of rows"
        assert counts[0] == 10000, f"Expected 10000 rows, got {counts[0]}"

    def test_multiple_threads_read_different_files(self, multiple_csv_files):
        """Test multiple threads reading from different files"""
        results = []
        errors = []

        def read_file(filepath, thread_id):
            try:
                count = 0
                with open_iterable(filepath) as source:
                    for row in source:
                        count += 1
                        assert "id" in row or "name" in row
                results.append((thread_id, count))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create threads, each reading a different file
        threads = []
        for i, filepath in enumerate(multiple_csv_files):
            thread = threading.Thread(target=read_file, args=(filepath, i))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)

        # Verify all threads completed successfully
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"

        # All files should have the same number of rows
        counts = [count for _, count in results]
        assert all(count == 1000 for count in counts), "Files have different row counts"

    def test_thread_pool_concurrent_read(self, shared_csv_file):
        """Test concurrent reading using ThreadPoolExecutor"""

        def read_file():
            count = 0
            with open_iterable(shared_csv_file) as source:
                for _row in source:
                    count += 1
            return count

        # Use ThreadPoolExecutor for concurrent execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(read_file) for _ in range(5)]
            results = [future.result(timeout=60) for future in concurrent.futures.as_completed(futures)]

        # All should read the same number of rows
        assert all(count == 10000 for count in results), "Threads read different numbers of rows"

    def test_concurrent_read_with_reset(self, shared_csv_file):
        """Test concurrent reading with reset operations"""
        results = []
        errors = []

        def read_with_reset(thread_id):
            try:
                count = 0
                with open_iterable(shared_csv_file) as source:
                    # Read some rows
                    for i, _row in enumerate(source):
                        count += 1
                        if i >= 99:
                            break

                    # Reset and read again
                    source.reset()
                    for i, _row in enumerate(source):
                        count += 1
                        if i >= 99:
                            break

                results.append((thread_id, count))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=read_with_reset, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=30)

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3


class TestConcurrentWrite:
    """Test concurrent writing to different files"""

    def test_multiple_threads_write_different_files(self, tmp_path):
        """Test multiple threads writing to different files"""
        results = []
        errors = []

        def write_file(thread_id):
            try:
                output_file = tmp_path / f"output_{thread_id}.csv"
                data = [{"id": i, "name": f"Person{i}"} for i in range(1000)]

                with open_iterable(output_file, "w") as dest:
                    dest.write_bulk(data)

                # Verify file was written
                assert output_file.exists()
                file_size = output_file.stat().st_size
                results.append((thread_id, file_size))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create 5 threads writing to different files
        threads = []
        for i in range(5):
            thread = threading.Thread(target=write_file, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=30)

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5

        # All files should have similar sizes
        sizes = [size for _, size in results]
        assert all(size > 0 for size in sizes), "Some files have zero size"
        # Sizes should be similar (within 10% variance)
        avg_size = sum(sizes) / len(sizes)
        assert all(abs(size - avg_size) / avg_size < 0.1 for size in sizes), "File sizes vary too much"

    def test_thread_pool_concurrent_write(self, tmp_path):
        """Test concurrent writing using ThreadPoolExecutor"""

        def write_file(thread_id):
            output_file = tmp_path / f"output_{thread_id}.csv"
            data = [{"id": i, "name": f"Person{i}"} for i in range(1000)]

            with open_iterable(output_file, "w") as dest:
                dest.write_bulk(data)

            return output_file.exists()

        # Use ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(write_file, i) for i in range(5)]
            results = [future.result(timeout=60) for future in concurrent.futures.as_completed(futures)]

        assert all(results), "Some files were not created"


class TestConcurrentFormatDetection:
    """Test concurrent format detection"""

    def test_concurrent_format_detection(self, multiple_csv_files):
        """Test concurrent format detection from multiple threads"""
        results = []
        errors = []

        def detect_format(filepath, thread_id):
            try:
                # Format detection happens in open_iterable
                with open_iterable(filepath) as source:
                    # Just verify it opened correctly
                    first_row = source.read()
                    assert first_row is not None
                results.append((thread_id, True))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create threads detecting formats concurrently
        threads = []
        for i, filepath in enumerate(multiple_csv_files):
            thread = threading.Thread(target=detect_format, args=(filepath, i))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=30)

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5


class TestConcurrentConversion:
    """Test concurrent format conversion"""

    def test_concurrent_conversion(self, multiple_csv_files, tmp_path):
        """Test concurrent conversion of multiple files"""
        from iterable.convert import convert

        results = []
        errors = []

        def convert_file(input_file, thread_id):
            try:
                output_file = tmp_path / f"output_{thread_id}.jsonl"
                convert(fromfile=str(input_file), tofile=str(output_file))
                results.append((thread_id, output_file.exists()))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create threads for concurrent conversion
        threads = []
        for i, input_file in enumerate(multiple_csv_files):
            thread = threading.Thread(target=convert_file, args=(input_file, i))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=60)

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        assert all(exists for _, exists in results), "Some conversions failed"


class TestThreadSafety:
    """Test thread safety of iterable operations"""

    def test_iterable_state_isolation(self, shared_csv_file):
        """Test that iterable state is isolated between threads"""
        results = []

        def read_with_state(thread_id):
            count = 0
            with open_iterable(shared_csv_file) as source:
                # Each thread should maintain its own position
                for i, _row in enumerate(source):
                    count += 1
                    if i >= 99:
                        break

                # Reset and verify we can read from beginning again
                source.reset()
                first_row_after_reset = source.read()
                assert first_row_after_reset is not None

            results.append((thread_id, count))

        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=read_with_state, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=30)

        assert len(results) == 3
        assert all(count == 100 for _, count in results), "Threads read different numbers of rows"

    def test_concurrent_context_managers(self, shared_csv_file):
        """Test that context managers work correctly with concurrent access"""
        results = []
        errors = []

        def use_context_manager(thread_id):
            try:
                # Each thread should have its own context
                with open_iterable(shared_csv_file) as source1:
                    count1 = 0
                    for i, _row in enumerate(source1):
                        count1 += 1
                        if i >= 49:
                            break

                    # Nested context manager in same thread
                    with open_iterable(shared_csv_file) as source2:
                        count2 = 0
                        for i, _row in enumerate(source2):
                            count2 += 1
                            if i >= 49:
                                break

                    # First source should still be valid
                    assert count1 == 50
                    assert count2 == 50

                results.append((thread_id, True))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=use_context_manager, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=30)

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3


class TestConcurrentBulkOperations:
    """Test concurrent bulk operations"""

    def test_concurrent_bulk_read(self, shared_csv_file):
        """Test concurrent bulk read operations"""
        results = []
        errors = []

        def bulk_read(thread_id):
            try:
                total_count = 0
                with open_iterable(shared_csv_file) as source:
                    while True:
                        chunk = source.read_bulk(num=1000)
                        if not chunk:
                            break
                        total_count += len(chunk)
                        assert len(chunk) > 0
                results.append((thread_id, total_count))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=bulk_read, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=30)

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3
        # All threads should read the same number of rows
        counts = [count for _, count in results]
        assert all(count == 10000 for count in counts), "Threads read different numbers of rows"

    def test_concurrent_bulk_write(self, tmp_path):
        """Test concurrent bulk write operations"""
        results = []
        errors = []

        def bulk_write(thread_id):
            try:
                output_file = tmp_path / f"bulk_output_{thread_id}.csv"
                data = [{"id": i, "name": f"Person{i}"} for i in range(1000)]

                with open_iterable(output_file, "w") as dest:
                    # Write in chunks
                    for i in range(0, len(data), 100):
                        chunk = data[i : i + 100]
                        dest.write_bulk(chunk)

                assert output_file.exists()
                results.append((thread_id, True))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=bulk_write, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=30)

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3


class TestConcurrentErrorHandling:
    """Test error handling with concurrent access"""

    def test_concurrent_error_handling(self, tmp_path):
        """Test that errors in one thread don't affect others"""
        # Create a file with some invalid data
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,valid\ninvalid_row\n2,valid\n")

        results = []
        errors = []

        def read_with_errors(thread_id):
            try:
                count = 0
                with open_iterable(test_file, iterableargs={"on_error": "skip"}) as source:
                    for _row in source:
                        count += 1
                results.append((thread_id, count))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=read_with_errors, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=30)

        # All threads should handle errors gracefully (on_error=skip)
        assert len(errors) == 0, f"Unexpected errors: {errors}"
        assert len(results) == 3
        # Each thread should read the 2 valid data rows (invalid_row skipped)
        counts = [count for _, count in results]
        assert all(c >= 1 for c in counts), "Some threads read no valid rows"
        assert sum(counts) >= 3, "Total valid rows read too low"
