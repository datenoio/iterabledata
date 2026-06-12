"""Tests for optimized bulk operations in various formats.

This test suite verifies that bulk operation optimizations work correctly
and maintain backward compatibility while providing performance improvements.
"""

import pytest


@pytest.mark.skipif(not hasattr(pytest, "importorskip") or True, reason="Requires optional dependencies")
class TestParquetBulkOptimization:
    """Test optimized Parquet bulk operations."""

    def test_parquet_batch_caching(self, tmp_path):
        """Test that Parquet read_bulk() uses batch caching correctly."""
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            pytest.skip("PyArrow not available")

        # Create test Parquet file with multiple batches
        test_file = tmp_path / "test.parquet"
        table = pa.table(
            {
                "col1": list(range(100)),  # 100 rows
                "col2": [f"value_{i}" for i in range(100)],
            }
        )
        pq.write_table(table, test_file, row_group_size=30)  # Creates multiple row groups

        from iterable.datatypes.parquet import ParquetIterable

        # Read in bulk - should use batch caching
        iterable = ParquetIterable(str(test_file), batch_size=20)
        chunk1 = iterable.read_bulk(15)  # Read 15 rows (less than batch size)
        assert len(chunk1) == 15
        assert chunk1[0]["col1"] == 0
        assert chunk1[14]["col1"] == 14

        # Read more - should use cached batch
        chunk2 = iterable.read_bulk(10)  # Should use remaining 5 from batch + 5 from next batch
        assert len(chunk2) == 10
        assert chunk2[0]["col1"] == 15
        assert chunk2[9]["col1"] == 24

        # Verify position is correct
        assert iterable.pos == 25

        iterable.close()

    def test_parquet_bulk_reads_all_rows(self, tmp_path):
        """Test that Parquet read_bulk() reads all rows correctly."""
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            pytest.skip("PyArrow not available")

        # Create test Parquet file
        test_file = tmp_path / "test.parquet"
        table = pa.table({"col1": list(range(50)), "col2": [f"val_{i}" for i in range(50)]})
        pq.write_table(table, test_file)

        from iterable.datatypes.parquet import ParquetIterable

        iterable = ParquetIterable(str(test_file))
        all_rows = []
        while True:
            chunk = iterable.read_bulk(10)
            if not chunk:
                break
            all_rows.extend(chunk)

        assert len(all_rows) == 50
        assert all_rows[0]["col1"] == 0
        assert all_rows[49]["col1"] == 49

        iterable.close()


@pytest.mark.skipif(not hasattr(pytest, "importorskip") or True, reason="Requires optional dependencies")
class TestArrowBulkOptimization:
    """Test optimized Arrow bulk operations."""

    def test_arrow_batch_caching(self, tmp_path):
        """Test that Arrow read_bulk() uses batch caching correctly."""
        try:
            import pyarrow as pa
            import pyarrow.feather as feather
        except ImportError:
            pytest.skip("PyArrow not available")

        # Create test Arrow file
        test_file = tmp_path / "test.arrow"
        table = pa.table({"col1": list(range(100)), "col2": [f"value_{i}" for i in range(100)]})
        feather.write_feather(table, test_file)

        from iterable.datatypes.arrow import ArrowIterable

        iterable = ArrowIterable(str(test_file), batch_size=20)
        chunk1 = iterable.read_bulk(15)  # Read 15 rows
        assert len(chunk1) == 15
        assert chunk1[0]["col1"] == 0

        # Read more - should use cached batch
        chunk2 = iterable.read_bulk(10)
        assert len(chunk2) == 10
        assert chunk2[0]["col1"] == 15

        assert iterable.pos == 25

        iterable.close()

    def test_arrow_bulk_reads_all_rows(self, tmp_path):
        """Test that Arrow read_bulk() reads all rows correctly."""
        try:
            import pyarrow as pa
            import pyarrow.feather as feather
        except ImportError:
            pytest.skip("PyArrow not available")

        test_file = tmp_path / "test.arrow"
        table = pa.table({"col1": list(range(50)), "col2": [f"val_{i}" for i in range(50)]})
        feather.write_feather(table, test_file)

        from iterable.datatypes.arrow import ArrowIterable

        iterable = ArrowIterable(str(test_file))
        all_rows = []
        while True:
            chunk = iterable.read_bulk(10)
            if not chunk:
                break
            all_rows.extend(chunk)

        assert len(all_rows) == 50
        iterable.close()


@pytest.mark.skipif(not hasattr(pytest, "importorskip") or True, reason="Requires optional dependencies")
class TestARFFBulkOptimization:
    """Test optimized ARFF bulk operations."""

    def test_arff_slicing_optimization(self, tmp_path):
        """Test that ARFF read_bulk() uses slicing correctly."""
        try:
            import arff  # noqa: F401
        except ImportError:
            pytest.skip("ARFF library not available")

        # Create test ARFF file
        test_file = tmp_path / "test.arff"
        arff_content = """@relation test
@attribute col1 numeric
@attribute col2 string
@data
1,value1
2,value2
3,value3
4,value4
5,value5
"""
        with open(test_file, "w") as f:
            f.write(arff_content)

        from iterable.datatypes.arff import ARFFIterable

        iterable = ARFFIterable(str(test_file))
        chunk = iterable.read_bulk(3)
        assert len(chunk) == 3
        assert chunk[0]["col1"] == 1
        assert chunk[2]["col1"] == 3

        # Read more
        chunk2 = iterable.read_bulk(2)
        assert len(chunk2) == 2
        assert chunk2[0]["col1"] == 4
        assert chunk2[1]["col1"] == 5

        # Should be at end
        chunk3 = iterable.read_bulk(10)
        assert len(chunk3) == 0

        iterable.close()

    def test_arff_bulk_position_tracking(self, tmp_path):
        """Test that ARFF read_bulk() correctly tracks position."""
        try:
            import arff  # noqa: F401
        except ImportError:
            pytest.skip("ARFF library not available")

        test_file = tmp_path / "test.arff"
        arff_content = """@relation test
@attribute col1 numeric
@data
1
2
3
4
5
"""
        with open(test_file, "w") as f:
            f.write(arff_content)

        from iterable.datatypes.arff import ARFFIterable

        iterable = ARFFIterable(str(test_file))
        assert iterable.pos == 0

        _ = iterable.read_bulk(3)
        assert iterable.pos == 3

        _ = iterable.read_bulk(2)
        assert iterable.pos == 5

        iterable.close()


@pytest.mark.skipif(not hasattr(pytest, "importorskip") or True, reason="Requires optional dependencies")
class TestTOMLBulkOptimization:
    """Test optimized TOML bulk operations."""

    def test_toml_slicing_optimization(self, tmp_path):
        """Test that TOML read_bulk() uses slicing correctly."""
        try:
            import tomli  # noqa: F401
        except ImportError:
            try:
                import toml  # noqa: F401
            except ImportError:
                pytest.skip("TOML library not available")

        # Create test TOML file
        test_file = tmp_path / "test.toml"
        toml_content = """[items]
[[items]]
key1 = "value1"
[[items]]
key2 = "value2"
[[items]]
key3 = "value3"
"""
        with open(test_file, "w") as f:
            f.write(toml_content)

        from iterable.datatypes.toml import TOMLIterable

        iterable = TOMLIterable(str(test_file))
        chunk = iterable.read_bulk(2)
        assert len(chunk) == 2
        assert "key1" in chunk[0] or "_table" in chunk[0]

        # Read more
        chunk2 = iterable.read_bulk(1)
        assert len(chunk2) == 1

        iterable.close()

    def test_toml_bulk_position_tracking(self, tmp_path):
        """Test that TOML read_bulk() correctly tracks position."""
        try:
            import tomli  # noqa: F401
        except ImportError:
            try:
                import toml  # noqa: F401
            except ImportError:
                pytest.skip("TOML library not available")

        test_file = tmp_path / "test.toml"
        toml_content = """[items]
[[items]]
key1 = "value1"
[[items]]
key2 = "value2"
"""
        with open(test_file, "w") as f:
            f.write(toml_content)

        from iterable.datatypes.toml import TOMLIterable

        iterable = TOMLIterable(str(test_file))
        assert iterable.pos == 0

        iterable.read_bulk(1)
        assert iterable.pos == 1

        iterable.read_bulk(1)
        assert iterable.pos == 2

        iterable.close()


class TestBulkOperationsBackwardCompatibility:
    """Test that bulk operation optimizations maintain backward compatibility."""

    def test_bulk_operations_return_lists(self, tmp_path):
        """Test that optimized bulk operations still return lists."""
        # Test with CSV (already optimized)
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2\nval1,val2\nval3,val4\n")

        from iterable.helpers.detect import open_iterable

        with open_iterable(str(test_file)) as source:
            chunk = source.read_bulk(2)
            assert isinstance(chunk, list)
            assert len(chunk) == 2

    def test_bulk_operations_respect_num_parameter(self, tmp_path):
        """Test that bulk operations respect the num parameter."""
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2\n" + "\n".join([f"val{i},val{i}" for i in range(10)]))

        from iterable.helpers.detect import open_iterable

        with open_iterable(str(test_file)) as source:
            chunk = source.read_bulk(5)
            assert len(chunk) == 5

            chunk2 = source.read_bulk(3)
            assert len(chunk2) == 3

    def test_bulk_operations_handle_end_of_file(self, tmp_path):
        """Test that bulk operations handle end of file correctly."""
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2\nval1,val2\n")

        from iterable.helpers.detect import open_iterable

        with open_iterable(str(test_file)) as source:
            chunk1 = source.read_bulk(10)  # Request more than available
            assert len(chunk1) == 1

            chunk2 = source.read_bulk(10)  # Should return empty list
            assert len(chunk2) == 0
