"""Tests for parallel processing support in IterableData."""

from iterable.convert import bulk_convert


class TestParallelBulkConvert:
    """Tests for parallel bulk conversion."""

    def test_parallel_bulk_convert_basic(self, tmp_path):
        """Test basic parallel bulk conversion."""
        # Create test files
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create multiple CSV files
        num_files = 5
        rows_per_file = 10
        for i in range(num_files):
            test_file = input_dir / f"test{i}.csv"
            content = "id,name\n"
            for j in range(rows_per_file):
                content += f"{j},test{j}\n"
            test_file.write_text(content)

        # Convert with parallel processing
        result = bulk_convert(
            str(input_dir / "*.csv"),
            str(output_dir),
            to_ext="jsonl",
            parallel=True,
            workers=2,
        )

        assert result.total_files == num_files
        assert result.successful_files == num_files
        assert result.failed_files == 0
        assert result.total_rows_in == num_files * rows_per_file
        assert result.total_rows_out == num_files * rows_per_file

        # Verify output files exist
        for i in range(num_files):
            output_file = output_dir / f"test{i}.jsonl"
            assert output_file.exists()

    def test_parallel_bulk_convert_default_workers(self, tmp_path):
        """Test parallel bulk conversion with default worker count."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create test files
        for i in range(3):
            test_file = input_dir / f"test{i}.csv"
            test_file.write_text("id,name\n1,test1\n2,test2\n")

        # Convert with parallel=True but workers=None (should use default)
        result = bulk_convert(
            str(input_dir / "*.csv"),
            str(output_dir),
            to_ext="jsonl",
            parallel=True,
            workers=None,
        )

        assert result.total_files == 3
        assert result.successful_files == 3
        assert result.failed_files == 0

    def test_parallel_bulk_convert_error_handling(self, tmp_path):
        """Test parallel bulk conversion continues after file failure."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create valid CSV file
        valid_file = input_dir / "valid.csv"
        valid_file.write_text("id,name\n1,test1\n2,test2\n")

        # Create invalid file (empty file that might cause issues)
        invalid_file = input_dir / "invalid.csv"
        invalid_file.write_text("")  # Empty file

        # Convert with parallel processing
        result = bulk_convert(
            str(input_dir / "*.csv"),
            str(output_dir),
            to_ext="jsonl",
            parallel=True,
            workers=2,
        )

        # Should have processed both files
        assert result.total_files == 2
        # At least one should succeed
        assert result.successful_files >= 1
        # Verify valid file was converted
        assert (output_dir / "valid.jsonl").exists()

    def test_parallel_bulk_convert_vs_sequential(self, tmp_path):
        """Test that parallel conversion produces same results as sequential."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir_parallel = tmp_path / "output_parallel"
        output_dir_parallel.mkdir()
        output_dir_sequential = tmp_path / "output_sequential"
        output_dir_sequential.mkdir()

        # Create test files
        num_files = 4
        for i in range(num_files):
            test_file = input_dir / f"test{i}.csv"
            test_file.write_text("id,name\n1,test1\n2,test2\n")

        # Convert with parallel processing
        result_parallel = bulk_convert(
            str(input_dir / "*.csv"),
            str(output_dir_parallel),
            to_ext="jsonl",
            parallel=True,
            workers=2,
        )

        # Convert sequentially
        result_sequential = bulk_convert(
            str(input_dir / "*.csv"),
            str(output_dir_sequential),
            to_ext="jsonl",
            parallel=False,
        )

        # Results should be identical
        assert result_parallel.total_files == result_sequential.total_files
        assert result_parallel.successful_files == result_sequential.successful_files
        assert result_parallel.total_rows_in == result_sequential.total_rows_in
        assert result_parallel.total_rows_out == result_sequential.total_rows_out

        # Verify output files have same content
        for i in range(num_files):
            parallel_file = output_dir_parallel / f"test{i}.jsonl"
            sequential_file = output_dir_sequential / f"test{i}.jsonl"
            assert parallel_file.exists()
            assert sequential_file.exists()
            # Compare file sizes (content should be same)
            assert parallel_file.stat().st_size == sequential_file.stat().st_size

    def test_parallel_bulk_convert_with_progress(self, tmp_path):
        """Test parallel bulk conversion with progress callback."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create test files
        for i in range(3):
            test_file = input_dir / f"test{i}.csv"
            test_file.write_text("id,name\n1,test1\n2,test2\n")

        # Track progress calls
        progress_calls = []

        def progress_callback(stats):
            progress_calls.append(stats)

        # Convert with parallel processing and progress callback
        result = bulk_convert(
            str(input_dir / "*.csv"),
            str(output_dir),
            to_ext="jsonl",
            parallel=True,
            workers=2,
            progress=progress_callback,
        )

        assert result.total_files == 3
        assert result.successful_files == 3
        # Progress callback should have been called
        assert len(progress_calls) > 0
        # Verify progress stats structure
        for call in progress_calls:
            assert "file_index" in call
            assert "total_files" in call
            assert "current_file" in call

    def test_parallel_bulk_convert_backward_compatibility(self, tmp_path):
        """Test that parallel=False (default) works as before."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create test files
        for i in range(3):
            test_file = input_dir / f"test{i}.csv"
            test_file.write_text("id,name\n1,test1\n2,test2\n")

        # Convert without parallel (default behavior)
        result = bulk_convert(
            str(input_dir / "*.csv"),
            str(output_dir),
            to_ext="jsonl",
            parallel=False,
        )

        assert result.total_files == 3
        assert result.successful_files == 3
        assert result.failed_files == 0

        # Verify output files exist
        for i in range(3):
            output_file = output_dir / f"test{i}.jsonl"
            assert output_file.exists()

    def test_parallel_bulk_convert_with_custom_workers(self, tmp_path):
        """Test parallel bulk conversion with custom worker count."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create test files
        num_files = 8
        for i in range(num_files):
            test_file = input_dir / f"test{i}.csv"
            test_file.write_text("id,name\n1,test1\n2,test2\n")

        # Convert with custom worker count
        result = bulk_convert(
            str(input_dir / "*.csv"),
            str(output_dir),
            to_ext="jsonl",
            parallel=True,
            workers=3,
        )

        assert result.total_files == num_files
        assert result.successful_files == num_files
        assert result.failed_files == 0

        # Verify all output files exist
        for i in range(num_files):
            output_file = output_dir / f"test{i}.jsonl"
            assert output_file.exists()

    def test_parallel_bulk_convert_with_atomic(self, tmp_path):
        """Test parallel bulk conversion with atomic writes."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create test files
        for i in range(3):
            test_file = input_dir / f"test{i}.csv"
            test_file.write_text("id,name\n1,test1\n2,test2\n")

        # Convert with parallel processing and atomic writes
        result = bulk_convert(
            str(input_dir / "*.csv"),
            str(output_dir),
            to_ext="jsonl",
            parallel=True,
            workers=2,
            atomic=True,
        )

        assert result.total_files == 3
        assert result.successful_files == 3
        assert result.failed_files == 0

        # Verify output files exist and no temp files remain
        for i in range(3):
            output_file = output_dir / f"test{i}.jsonl"
            assert output_file.exists()
            # Verify no temp files
            temp_file = output_dir / f"test{i}.jsonl.tmp"
            assert not temp_file.exists()

    def test_parallel_bulk_convert_with_iterableargs(self, tmp_path):
        """Test parallel bulk conversion with custom iterableargs."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create CSV files with custom delimiter
        for i in range(2):
            test_file = input_dir / f"test{i}.csv"
            test_file.write_text("id|name\n1|test1\n2|test2\n")

        # Convert with custom delimiter in iterableargs
        result = bulk_convert(
            str(input_dir / "*.csv"),
            str(output_dir),
            to_ext="jsonl",
            parallel=True,
            workers=2,
            iterableargs={"delimiter": "|"},
        )

        assert result.total_files == 2
        assert result.successful_files == 2
        assert result.failed_files == 0

        # Verify output files exist
        for i in range(2):
            output_file = output_dir / f"test{i}.jsonl"
            assert output_file.exists()
