"""Tests for progress callback enhancements."""

from iterable.convert.core import convert
from iterable.helpers.detect import open_iterable
from iterable.helpers.progress import with_progress
from iterable.pipeline.core import pipeline


class TestConfigurableProgressInterval:
    """Test configurable progress interval."""

    def test_convert_with_custom_interval(self, tmp_path):
        """Test convert() with custom progress interval."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"

        # Create test data
        input_file.write_text("col1,col2\n1,2\n3,4\n5,6\n7,8\n9,10\n")

        callback_counts = []

        def progress_callback(stats):
            callback_counts.append(stats["rows_read"])

        result = convert(
            str(input_file),
            str(output_file),
            progress=progress_callback,
            progress_interval=2,  # Call every 2 rows
        )

        # Should be called at rows 2, 4, and final (5)
        assert len(callback_counts) >= 2
        assert 2 in callback_counts
        assert 4 in callback_counts
        assert result.rows_in == 5

    def test_pipeline_with_custom_interval(self, tmp_path):
        """Test pipeline() with custom progress interval."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"

        input_file.write_text("col1,col2\n1,2\n3,4\n5,6\n7,8\n9,10\n")

        callback_counts = []

        def progress_callback(stats):
            callback_counts.append(stats["rows_processed"])

        def process_func(row, state):
            return row

        with open_iterable(str(input_file)) as source:
            with open_iterable(str(output_file), mode="w", iterableargs={"keys": ["col1", "col2"]}) as dest:
                result = pipeline(
                    source,
                    dest,
                    process_func=process_func,
                    progress=progress_callback,
                    progress_interval=2,  # Call every 2 rows
                )

        assert len(callback_counts) >= 2
        assert result.rows_processed == 5


class TestEnhancedProgressStats:
    """Test enhanced progress stats."""

    def test_convert_with_enhanced_stats(self, tmp_path):
        """Test convert() progress callback receives enhanced stats."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"

        input_file.write_text("col1,col2\n" + "\n".join([f"{i},{i * 2}" for i in range(100)]))

        received_stats = []

        def progress_callback(stats):
            received_stats.append(stats.copy())

        convert(
            str(input_file),
            str(output_file),
            progress=progress_callback,
            progress_interval=50,
            use_totals=True,
        )

        # Check that enhanced stats are present
        assert len(received_stats) > 0
        last_stats = received_stats[-1]

        # Check for enhanced fields
        assert "rows_read" in last_stats
        assert "rows_written" in last_stats
        assert "elapsed" in last_stats
        assert "bytes_read" in last_stats
        assert "bytes_written" in last_stats
        assert "percent_complete" in last_stats or last_stats.get("estimated_total") is None
        assert "estimated_time_remaining" in last_stats or last_stats.get("estimated_total") is None

        # Verify percent_complete calculation when estimated_total is available
        if last_stats.get("estimated_total") is not None:
            assert last_stats["percent_complete"] is not None
            assert 0 <= last_stats["percent_complete"] <= 100

    def test_enhanced_stats_with_totals(self, tmp_path):
        """Test enhanced stats calculation with totals."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"

        # Create file with known row count
        rows = ["col1,col2"] + [f"{i},{i * 2}" for i in range(100)]
        input_file.write_text("\n".join(rows))

        received_stats = []

        def progress_callback(stats):
            received_stats.append(stats.copy())

        convert(
            str(input_file),
            str(output_file),
            progress=progress_callback,
            progress_interval=25,
            use_totals=True,
        )

        # Check that percent_complete is calculated correctly
        for stats in received_stats:
            if stats.get("estimated_total") is not None and stats.get("rows_read", 0) > 0:
                expected_percent = (stats["rows_read"] / stats["estimated_total"]) * 100.0
                assert abs(stats["percent_complete"] - expected_percent) < 0.1


class TestWithProgressHelper:
    """Test with_progress() helper function."""

    def test_with_progress_basic(self, tmp_path):
        """Test basic with_progress() usage."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("col1,col2\n1,2\n3,4\n5,6\n")

        callback_counts = []

        def progress_callback(stats):
            callback_counts.append(stats["rows_read"])

        with open_iterable(str(input_file)) as source:
            rows = list(with_progress(source, callback=progress_callback, interval=2))

        assert len(rows) == 3
        assert len(callback_counts) >= 1
        assert 2 in callback_counts  # Called at row 2
        assert callback_counts[-1] == 3  # Final callback

    def test_with_progress_stats(self, tmp_path):
        """Test with_progress() provides correct stats."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("col1,col2\n" + "\n".join([f"{i},{i * 2}" for i in range(50)]))

        received_stats = []

        def progress_callback(stats):
            received_stats.append(stats.copy())

        with open_iterable(str(input_file)) as source:
            list(with_progress(source, callback=progress_callback, interval=10))

        # Check stats structure
        assert len(received_stats) > 0
        last_stats = received_stats[-1]

        assert "rows_read" in last_stats
        assert "elapsed" in last_stats
        assert "throughput" in last_stats
        assert last_stats["rows_read"] == 50
        assert last_stats["elapsed"] >= 0
        assert last_stats["throughput"] is not None

    def test_with_progress_callback_error_handling(self, tmp_path):
        """Test that callback errors don't break iteration."""
        input_file = tmp_path / "input.csv"
        input_file.write_text("col1,col2\n1,2\n3,4\n5,6\n")

        def failing_callback(stats):
            raise ValueError("Callback error")

        # Should not raise exception
        with open_iterable(str(input_file)) as source:
            rows = list(with_progress(source, callback=failing_callback, interval=1))

        assert len(rows) == 3


class TestBackwardCompatibility:
    """Test backward compatibility of progress callbacks."""

    def test_default_interval_unchanged(self, tmp_path):
        """Test that default interval behavior is unchanged."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"

        # Create file with more than 1000 rows to trigger default interval
        rows = ["col1,col2"] + [f"{i},{i * 2}" for i in range(1500)]
        input_file.write_text("\n".join(rows))

        callback_counts = []

        def progress_callback(stats):
            callback_counts.append(stats["rows_read"])

        result = convert(
            str(input_file),
            str(output_file),
            progress=progress_callback,
            # progress_interval not specified - should use default 1000
        )

        # Should be called at 1000 and final (1500)
        assert len(callback_counts) >= 1
        assert 1000 in callback_counts
        assert result.rows_in == 1500
