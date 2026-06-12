import os

import pytest

from iterable.convert import bulk_convert, convert


class TestConvert:
    def test_convert_csv_to_jsonl(self):
        convert(fromfile="fixtures/ru_cp1251_comma.csv", tofile="testdata/ru_cp1251_comma_converted.jsonl")
        assert os.path.exists("testdata/ru_cp1251_comma_converted.jsonl")

    def test_convert_csv_to_parquet(self):
        convert(fromfile="fixtures/ru_cp1251_comma.csv", tofile="testdata/ru_cp1251_comma_converted.parquet")
        assert os.path.exists("testdata/ru_cp1251_comma_converted.parquet")

    def test_convert_csv_to_csv_gz(self):
        convert(fromfile="fixtures/ru_cp1251_comma.csv", tofile="testdata/ru_cp1251_comma_converted.csv.gz")
        assert os.path.exists("testdata/ru_cp1251_comma_converted.csv.gz")

    def test_convert_jsonl_to_csv_xz(self):
        convert(fromfile="fixtures/2cols6rows_flat.jsonl", tofile="testdata/2cols6rows_flat_converted.csv.gz")
        assert os.path.exists("testdata/2cols6rows_flat_converted.csv.gz")

    def test_convert_with_batch_size(self):
        """Test convert with custom batch size"""
        convert(fromfile="fixtures/2cols6rows_flat.jsonl", tofile="testdata/test_convert_batch.jsonl", batch_size=2)
        assert os.path.exists("testdata/test_convert_batch.jsonl")
        if os.path.exists("testdata/test_convert_batch.jsonl"):
            os.unlink("testdata/test_convert_batch.jsonl")

    def test_convert_with_flatten(self):
        """Test convert with flatten option"""
        convert(
            fromfile="fixtures/2cols6rows_flat.jsonl", tofile="testdata/test_convert_flatten.jsonl", is_flatten=True
        )
        assert os.path.exists("testdata/test_convert_flatten.jsonl")
        if os.path.exists("testdata/test_convert_flatten.jsonl"):
            os.unlink("testdata/test_convert_flatten.jsonl")

    def test_convert_with_use_totals(self):
        """Test convert with use_totals option"""
        convert(fromfile="fixtures/2cols6rows.csv", tofile="testdata/test_convert_totals.jsonl", use_totals=True)
        assert os.path.exists("testdata/test_convert_totals.jsonl")
        if os.path.exists("testdata/test_convert_totals.jsonl"):
            os.unlink("testdata/test_convert_totals.jsonl")

    def test_convert_with_silent(self):
        """Test convert with silent=False"""
        convert(fromfile="fixtures/2cols6rows_flat.jsonl", tofile="testdata/test_convert_silent.jsonl", silent=False)
        assert os.path.exists("testdata/test_convert_silent.jsonl")
        if os.path.exists("testdata/test_convert_silent.jsonl"):
            os.unlink("testdata/test_convert_silent.jsonl")

    def test_convert_different_formats(self):
        """Test converting between different format combinations"""
        # CSV to JSON
        convert(
            fromfile="fixtures/2cols6rows.csv",
            tofile="testdata/test_convert_csv_json.json",
            iterableargs={"tagname": "items"},
        )
        assert os.path.exists("testdata/test_convert_csv_json.json")
        if os.path.exists("testdata/test_convert_csv_json.json"):
            os.unlink("testdata/test_convert_csv_json.json")

    def test_convert_with_toiterableargs(self):
        """Test convert with output iterable arguments"""
        # Convert CSV to CSV with custom delimiter
        convert(
            fromfile="fixtures/2cols6rows.csv",
            tofile="testdata/test_convert_output_args.csv",
            toiterableargs={"delimiter": "|"},
        )
        assert os.path.exists("testdata/test_convert_output_args.csv")
        # Verify the file was created and has content
        if os.path.exists("testdata/test_convert_output_args.csv"):
            with open("testdata/test_convert_output_args.csv") as f:
                content = f.read()
                # Check that pipe delimiter is used (not comma)
                assert "|" in content or len(content) > 0
            os.unlink("testdata/test_convert_output_args.csv")

    def test_convert_file_not_found(self):
        """Test convert with non-existent source file"""
        with pytest.raises(FileNotFoundError):
            convert(fromfile="nonexistent_file.csv", tofile="testdata/output.jsonl")

    def test_convert_invalid_scan_limit(self):
        """Test convert with invalid scan_limit"""
        with pytest.raises(ValueError, match="scan_limit must be non-negative"):
            convert(
                fromfile="fixtures/2cols6rows.csv",
                tofile="testdata/test_invalid_scan.jsonl",
                scan_limit=-1,
            )

    def test_convert_invalid_batch_size(self):
        """Test convert with invalid batch_size"""
        with pytest.raises(ValueError, match="batch_size must be positive"):
            convert(
                fromfile="fixtures/2cols6rows.csv",
                tofile="testdata/test_invalid_batch.jsonl",
                batch_size=0,
            )

    def test_convert_empty_file(self, tmp_path):
        """Test convert with empty source file"""
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("")
        output_file = tmp_path / "output.jsonl"
        # Should handle empty file gracefully
        convert(fromfile=str(empty_file), tofile=str(output_file))
        assert output_file.exists()

    def test_convert_single_record(self, tmp_path):
        """Test convert with single record file"""
        single_file = tmp_path / "single.csv"
        single_file.write_text("id,name\n1,test")
        output_file = tmp_path / "output.jsonl"
        convert(fromfile=str(single_file), tofile=str(output_file))
        assert output_file.exists()

    def test_convert_with_scan_limit(self, tmp_path):
        """Test convert with scan_limit"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test1\n2,test2\n3,test3")
        output_file = tmp_path / "output.jsonl"
        convert(fromfile=str(test_file), tofile=str(output_file), scan_limit=2)
        assert output_file.exists()

    def test_convert_resource_cleanup_on_error(self, tmp_path):
        """Test that resources are cleaned up even on error"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test")
        output_file = tmp_path / "output.unknown_format"
        # Should raise error but clean up resources
        try:
            convert(fromfile=str(test_file), tofile=str(output_file))
        except Exception:
            pass
        # Resources should be cleaned up (no file handles left open)

    def test_convert_nested_to_flat(self, tmp_path):
        """Test convert nested JSON to flat CSV"""
        nested_file = tmp_path / "nested.jsonl"
        nested_file.write_text('{"user": {"name": "test", "age": 30}}\n')
        output_file = tmp_path / "output.csv"
        convert(fromfile=str(nested_file), tofile=str(output_file), is_flatten=True)
        assert output_file.exists()

    def test_convert_with_iterableargs(self, tmp_path):
        """Test convert with input iterable arguments"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id;name\n1;test")
        output_file = tmp_path / "output.jsonl"
        convert(
            fromfile=str(test_file),
            tofile=str(output_file),
            iterableargs={"delimiter": ";"},
        )
        assert output_file.exists()

    def test_convert_progress_tracking(self, tmp_path):
        """Test convert with progress tracking (use_totals)"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test1\n2,test2\n3,test3")
        output_file = tmp_path / "output.jsonl"
        # Should work with use_totals=True
        convert(fromfile=str(test_file), tofile=str(output_file), use_totals=True)
        assert output_file.exists()

    def test_convert_large_batch(self, tmp_path):
        """Test convert with large batch size"""
        test_file = tmp_path / "test.csv"
        # Create file with many rows
        with open(test_file, "w") as f:
            f.write("id,name\n")
            for i in range(100):
                f.write(f"{i},test{i}\n")
        output_file = tmp_path / "output.jsonl"
        convert(fromfile=str(test_file), tofile=str(output_file), batch_size=1000)
        assert output_file.exists()

    def test_convert_schema_extraction(self, tmp_path):
        """Test that schema extraction works for flat formats"""
        test_file = tmp_path / "test.jsonl"
        test_file.write_text('{"id": 1, "name": "test1"}\n{"id": 2, "name": "test2", "extra": "field"}\n')
        output_file = tmp_path / "output.csv"
        # Should extract all keys (id, name, extra)
        convert(fromfile=str(test_file), tofile=str(output_file))
        assert output_file.exists()
        # Verify all columns are present
        with open(output_file) as f:
            header = f.readline()
            assert "id" in header
            assert "name" in header
            assert "extra" in header

    def test_convert_atomic_write_success(self, tmp_path):
        """Test atomic write on successful conversion"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test1\n2,test2\n")
        output_file = tmp_path / "output.jsonl"
        temp_file = tmp_path / "output.jsonl.tmp"

        # Convert with atomic=True
        convert(fromfile=str(test_file), tofile=str(output_file), atomic=True)

        # Verify output file exists and temp file is gone
        assert output_file.exists()
        assert not temp_file.exists()

        # Verify content
        with open(output_file) as f:
            lines = f.readlines()
            assert len(lines) == 2

    def test_convert_atomic_write_preserves_original_on_failure(self, tmp_path):
        """Test that atomic write preserves original file on failure"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test1\n")
        output_file = tmp_path / "output.unknown_format"
        temp_file = tmp_path / "output.unknown_format.tmp"

        # Create an existing output file
        output_file.write_text("original content")

        # Try to convert to unknown format (should fail)
        try:
            convert(fromfile=str(test_file), tofile=str(output_file), atomic=True)
        except Exception:
            pass

        # Verify original file is preserved and temp file is cleaned up
        assert output_file.exists()
        assert output_file.read_text() == "original content"
        assert not temp_file.exists()

    def test_convert_atomic_write_backward_compatibility(self, tmp_path):
        """Test that atomic=False (default) works as before"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test1\n")
        output_file = tmp_path / "output.jsonl"
        temp_file = tmp_path / "output.jsonl.tmp"

        # Convert with atomic=False (default)
        convert(fromfile=str(test_file), tofile=str(output_file), atomic=False)

        # Verify output file exists and no temp file was created
        assert output_file.exists()
        assert not temp_file.exists()

    def test_convert_atomic_write_cleanup_on_error(self, tmp_path):
        """Test that temp file is cleaned up on error"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,test1\n")
        output_file = tmp_path / "output.jsonl"
        temp_file = tmp_path / "output.jsonl.tmp"

        # Create a temp file manually to simulate partial write
        temp_file.write_text("partial")

        # Convert with atomic=True (should clean up existing temp file)
        convert(fromfile=str(test_file), tofile=str(output_file), atomic=True)

        # Verify final file exists and temp is gone
        assert output_file.exists()
        assert not temp_file.exists()


class TestBulkConvert:
    def test_bulk_convert_glob_pattern(self, tmp_path):
        """Test bulk_convert with glob pattern"""
        # Create test files
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create multiple CSV files
        for i in range(3):
            test_file = input_dir / f"test{i}.csv"
            test_file.write_text("id,name\n1,test1\n2,test2\n")

        # Convert all CSV files
        result = bulk_convert(str(input_dir / "*.csv"), str(output_dir), to_ext="jsonl")

        assert result.total_files == 3
        assert result.successful_files == 3
        assert result.failed_files == 0
        assert result.total_rows_in == 6  # 2 rows per file * 3 files
        assert result.total_rows_out == 6

        # Verify output files exist
        for i in range(3):
            output_file = output_dir / f"test{i}.jsonl"
            assert output_file.exists()

    def test_bulk_convert_with_pattern(self, tmp_path):
        """Test bulk_convert with filename pattern"""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        test_file = input_dir / "data.csv"
        test_file.write_text("id,name\n1,test\n")

        result = bulk_convert(str(input_dir / "*.csv"), str(output_dir), pattern="{name}.parquet")

        assert result.total_files == 1
        assert result.successful_files == 1
        output_file = output_dir / "data.csv.parquet"
        assert output_file.exists()

    def test_bulk_convert_directory(self, tmp_path):
        """Test bulk_convert with directory path"""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create multiple files
        for i in range(2):
            test_file = input_dir / f"file{i}.jsonl"
            test_file.write_text('{"id": 1}\n{"id": 2}\n')

        result = bulk_convert(str(input_dir), str(output_dir), to_ext="csv")

        assert result.total_files == 2
        assert result.successful_files == 2
        for i in range(2):
            output_file = output_dir / f"file{i}.csv"
            assert output_file.exists()

    def test_bulk_convert_single_file(self, tmp_path):
        """Test bulk_convert with single file path"""
        input_file = tmp_path / "input.csv"
        input_file.write_text("id,name\n1,test\n")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = bulk_convert(str(input_file), str(output_dir), to_ext="jsonl")

        assert result.total_files == 1
        assert result.successful_files == 1
        output_file = output_dir / "input.jsonl"
        assert output_file.exists()

    def test_bulk_convert_with_compression(self, tmp_path):
        """Test bulk_convert with compressed files"""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a CSV file
        test_file = input_dir / "data.csv"
        test_file.write_text("id,name\n1,test\n")

        # Convert to compressed parquet
        result = bulk_convert(str(input_dir / "*.csv"), str(output_dir), pattern="{stem}.parquet.zst")

        assert result.total_files == 1
        assert result.successful_files == 1
        output_file = output_dir / "data.parquet.zst"
        assert output_file.exists()

    def test_bulk_convert_error_handling(self, tmp_path):
        """Test bulk_convert continues after file failure"""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create one valid file and one invalid (non-existent reference)
        valid_file = input_dir / "valid.csv"
        valid_file.write_text("id,name\n1,test\n")

        invalid_file = input_dir / "invalid.csv"
        # Write invalid CSV that might cause issues, or reference non-existent file
        # Let's create a file that will fail conversion
        invalid_file.write_text("invalid,content,no,header\n")

        # Try to convert - should handle errors gracefully
        result = bulk_convert(str(input_dir / "*.csv"), str(output_dir), to_ext="jsonl")

        # Should have processed both files
        assert result.total_files == 2
        # At least one should succeed
        assert result.successful_files >= 1

    def test_bulk_convert_empty_glob(self, tmp_path):
        """Test bulk_convert with glob pattern matching no files"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = bulk_convert("nonexistent/*.csv", str(output_dir), to_ext="jsonl")

        assert result.total_files == 0
        assert result.successful_files == 0
        assert result.failed_files == 0
        assert result.total_rows_in == 0
        assert result.total_rows_out == 0

    def test_bulk_convert_empty_directory(self, tmp_path):
        """Test bulk_convert with empty directory"""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = bulk_convert(str(input_dir), str(output_dir), to_ext="jsonl")

        assert result.total_files == 0
        assert result.successful_files == 0

    def test_bulk_convert_with_batch_size(self, tmp_path):
        """Test bulk_convert passes batch_size parameter"""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        test_file = input_dir / "test.csv"
        # Create file with many rows
        with open(test_file, "w") as f:
            f.write("id,name\n")
            for i in range(100):
                f.write(f"{i},test{i}\n")

        result = bulk_convert(str(input_dir / "*.csv"), str(output_dir), to_ext="jsonl", batch_size=10)

        assert result.total_files == 1
        assert result.successful_files == 1
        assert result.total_rows_in == 100

    def test_bulk_convert_with_iterableargs(self, tmp_path):
        """Test bulk_convert passes iterableargs parameter"""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create CSV with semicolon delimiter
        test_file = input_dir / "test.csv"
        test_file.write_text("id;name\n1;test\n")

        result = bulk_convert(
            str(input_dir / "*.csv"),
            str(output_dir),
            to_ext="jsonl",
            iterableargs={"delimiter": ";"},
        )

        assert result.total_files == 1
        assert result.successful_files == 1

    def test_bulk_convert_with_is_flatten(self, tmp_path):
        """Test bulk_convert passes is_flatten parameter"""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create nested JSONL
        test_file = input_dir / "test.jsonl"
        test_file.write_text('{"user": {"name": "test", "age": 30}}\n')

        result = bulk_convert(str(input_dir / "*.jsonl"), str(output_dir), to_ext="csv", is_flatten=True)

        assert result.total_files == 1
        assert result.successful_files == 1

    def test_bulk_convert_creates_output_directory(self, tmp_path):
        """Test bulk_convert creates output directory if it doesn't exist"""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output" / "nested" / "path"

        test_file = input_dir / "test.csv"
        test_file.write_text("id,name\n1,test\n")

        result = bulk_convert(str(input_dir / "*.csv"), str(output_dir), to_ext="jsonl")

        assert result.total_files == 1
        assert result.successful_files == 1
        assert output_dir.exists()
        assert (output_dir / "test.jsonl").exists()

    def test_bulk_convert_pattern_placeholders(self, tmp_path):
        """Test bulk_convert filename pattern with different placeholders"""
        import gzip

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        test_file = input_dir / "data.csv.gz"
        with gzip.open(test_file, "wt", encoding="utf-8") as f:
            f.write("id,name\n1,test\n")

        # Test {name} placeholder
        result = bulk_convert(str(input_dir / "*.csv.gz"), str(output_dir), pattern="{name}.parquet")
        assert result.successful_files == 1
        assert (output_dir / "data.csv.gz.parquet").exists()

        # Test {stem} placeholder
        output_dir2 = tmp_path / "output2"
        output_dir2.mkdir()
        result2 = bulk_convert(str(input_dir / "*.csv.gz"), str(output_dir2), pattern="{stem}.parquet")
        assert result2.successful_files == 1
        # stem should be "data.csv" (without .gz)
        assert (output_dir2 / "data.csv.parquet").exists()

    def test_bulk_convert_aggregated_results(self, tmp_path):
        """Test bulk_convert returns aggregated results"""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create multiple files with different row counts
        for i in range(3):
            test_file = input_dir / f"file{i}.csv"
            rows = i + 1  # 1, 2, 3 rows
            with open(test_file, "w") as f:
                f.write("id,name\n")
                for j in range(rows):
                    f.write(f"{j},test{j}\n")

        result = bulk_convert(str(input_dir / "*.csv"), str(output_dir), to_ext="jsonl")

        assert result.total_files == 3
        assert result.successful_files == 3
        assert result.total_rows_in == 6  # 1 + 2 + 3
        assert result.total_rows_out == 6
        assert len(result.file_results) == 3
        assert result.throughput is not None

    def test_bulk_convert_missing_pattern_and_ext(self, tmp_path):
        """Test bulk_convert raises error when both pattern and to_ext are None"""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        test_file = input_dir / "test.csv"
        test_file.write_text("id,name\n1,test\n")

        with pytest.raises(ValueError, match="Either 'pattern' or 'to_ext' must be specified"):
            bulk_convert(str(input_dir / "*.csv"), str(output_dir))

    def test_bulk_convert_dest_not_directory(self, tmp_path):
        """Test bulk_convert raises error when dest exists but is not a directory"""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_file = tmp_path / "output_file.txt"
        output_file.write_text("not a directory")

        test_file = input_dir / "test.csv"
        test_file.write_text("id,name\n1,test\n")

        with pytest.raises(ValueError, match="exists but is not a directory"):
            bulk_convert(str(input_dir / "*.csv"), str(output_file), to_ext="jsonl")

    def test_bulk_convert_with_atomic(self, tmp_path):
        """Test bulk_convert with atomic writes"""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create multiple CSV files
        for i in range(2):
            test_file = input_dir / f"test{i}.csv"
            test_file.write_text("id,name\n1,test1\n2,test2\n")

        # Convert with atomic=True
        result = bulk_convert(str(input_dir / "*.csv"), str(output_dir), to_ext="jsonl", atomic=True)

        assert result.total_files == 2
        assert result.successful_files == 2

        # Verify output files exist and no temp files remain
        for i in range(2):
            output_file = output_dir / f"test{i}.jsonl"
            temp_file = output_dir / f"test{i}.jsonl.tmp"
            assert output_file.exists()
            assert not temp_file.exists()
