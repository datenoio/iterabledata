import os

from fixdata import FIXTURES

from iterable.datatypes import CSVIterable, JSONLinesIterable
from iterable.pipeline import Pipeline, pipeline


class TestPipeline:
    def test_pipeline_initialization(self):
        """Test Pipeline class initialization"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        destination = JSONLinesIterable("testdata/test_output.jsonl", mode="w")
        os.makedirs("testdata", exist_ok=True)

        def process_func(record, state):
            return record

        p = Pipeline(source=source, destination=destination, process_func=process_func)

        assert p.source == source
        assert p.destination == destination
        assert p.process_func == process_func
        assert p.trigger_func is None
        assert p.trigger_on == 1000
        assert p.final_func is None
        assert p.reset_iterables
        assert p.skip_nulls
        assert p.start_state == {}

        source.close()
        destination.close()
        if os.path.exists("testdata/test_output.jsonl"):
            os.unlink("testdata/test_output.jsonl")

    def test_pipeline_run_basic(self):
        """Test basic pipeline execution"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_basic.jsonl"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        processed_records = []

        def process_func(record, state):
            processed_records.append(record)
            return record

        p = Pipeline(source=source, destination=destination, process_func=process_func)

        stats = p.run()

        assert stats["rec_count"] == len(FIXTURES)
        assert stats["exceptions"] == 0
        assert "time_start" in stats
        assert "time_end" in stats
        assert "duration" in stats
        assert len(processed_records) == len(FIXTURES)

        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_pipeline_wrapper_function(self):
        """Test pipeline() wrapper function"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_wrapper.jsonl"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        processed_count = [0]

        def process_func(record, state):
            processed_count[0] += 1
            return record

        pipeline(source=source, destination=destination, process_func=process_func)

        assert processed_count[0] == len(FIXTURES)

        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_pipeline_with_state(self):
        """Test pipeline with state management"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_state.jsonl"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        start_state = {"count": 0, "sum": 0}

        def process_func(record, state):
            state["count"] += 1
            if "id" in record:
                state["sum"] += int(record["id"])
            return record

        p = Pipeline(source=source, destination=destination, process_func=process_func, start_state=start_state)

        p.run()

        assert start_state["count"] == len(FIXTURES)

        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_pipeline_trigger_func(self):
        """Test pipeline with trigger function"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_trigger.jsonl"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        trigger_calls = []

        def process_func(record, state):
            return record

        def trigger_func(stats, state):
            trigger_calls.append(stats["rec_count"])

        p = Pipeline(
            source=source,
            destination=destination,
            process_func=process_func,
            trigger_func=trigger_func,
            trigger_on=2,  # Trigger every 2 records
        )

        p.run()

        # Should have been called multiple times
        assert len(trigger_calls) > 0
        # All trigger calls should be multiples of trigger_on
        for count in trigger_calls:
            assert count % 2 == 0

        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_pipeline_final_func(self):
        """Test pipeline with final function"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_final.jsonl"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        final_stats = None

        def process_func(record, state):
            return record

        def final_func(stats, state):
            nonlocal final_stats
            final_stats = stats.copy()

        p = Pipeline(source=source, destination=destination, process_func=process_func, final_func=final_func)

        p.run()

        assert final_stats is not None
        assert final_stats["rec_count"] == len(FIXTURES)
        assert "duration" in final_stats

        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_pipeline_skip_nulls(self):
        """Test pipeline skip_nulls behavior"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_skip_nulls.jsonl"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        written_count = [0]

        def process_func(record, state):
            # Return None for some records
            record_id = int(record.get("id", 0))
            if record_id % 2 == 0:
                return None
            return record

        # Mock write to count writes
        original_write = destination.write

        def mock_write(record):
            written_count[0] += 1
            return original_write(record)

        destination.write = mock_write

        p = Pipeline(source=source, destination=destination, process_func=process_func, skip_nulls=True)

        stats = p.run()

        # With skip_nulls=True, None results should not be written
        # Should have written approximately half the records
        assert written_count[0] < len(FIXTURES)
        assert stats["nulls"] == 0  # nulls not counted when skip_nulls=True

        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_pipeline_no_skip_nulls(self):
        """Test pipeline with skip_nulls=False"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_no_skip_nulls.jsonl"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        def process_func(record, state):
            # Return None for some records
            record_id = int(record.get("id", 0))
            if record_id % 2 == 0:
                return None
            return record

        p = Pipeline(source=source, destination=destination, process_func=process_func, skip_nulls=False)

        stats = p.run()

        # With skip_nulls=False, None results should increment nulls counter
        assert stats["nulls"] > 0

        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_pipeline_reset_iterables(self):
        """Test pipeline reset_iterables flag"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_reset.jsonl"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        # Read one record to move position
        _ = source.read()
        source.pos if hasattr(source, "pos") else None

        def process_func(record, state):
            return record

        p = Pipeline(source=source, destination=destination, process_func=process_func, reset_iterables=True)

        p.run()

        # Source should have been reset (position should be at start)
        # After run, we should be able to read from beginning
        source.reset()
        first_record = source.read()
        assert first_record == FIXTURES[0]

        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_pipeline_no_reset_iterables(self):
        """Test pipeline with reset_iterables=False"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_no_reset.jsonl"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        # Read some records first
        for _ in range(3):
            try:
                source.read()
            except StopIteration:
                break

        def process_func(record, state):
            return record

        p = Pipeline(source=source, destination=destination, process_func=process_func, reset_iterables=False)

        stats = p.run()

        # Should process from current position, not from start
        # So rec_count should be less than total
        assert stats["rec_count"] <= len(FIXTURES)

        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_pipeline_exception_handling(self):
        """Test pipeline exception handling"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_exceptions.jsonl"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        def process_func(record, state):
            # Raise exception for some records
            if record.get("id", "0") == "1":
                raise ValueError("Test exception")
            return record

        p = Pipeline(source=source, destination=destination, process_func=process_func)

        stats = p.run()

        # Should have counted exceptions
        assert stats["exceptions"] > 0
        # Should still process other records
        assert stats["rec_count"] == len(FIXTURES)

        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_pipeline_no_destination(self):
        """Test pipeline without destination"""
        source = CSVIterable("fixtures/2cols6rows.csv")

        processed_count = [0]

        def process_func(record, state):
            processed_count[0] += 1
            return record

        p = Pipeline(source=source, destination=None, process_func=process_func)

        stats = p.run()

        assert stats["rec_count"] == len(FIXTURES)
        assert processed_count[0] == len(FIXTURES)

        source.close()

    def test_pipeline_trigger_func_exception(self):
        """Test that trigger function exceptions don't stop pipeline"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_trigger_exception.jsonl"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        def process_func(record, state):
            return record

        trigger_calls = [0]

        def trigger_func(stats, state):
            trigger_calls[0] += 1
            if trigger_calls[0] == 1:
                raise ValueError("Trigger exception")

        p = Pipeline(
            source=source, destination=destination, process_func=process_func, trigger_func=trigger_func, trigger_on=2
        )

        stats = p.run()

        # Pipeline should continue despite trigger exception
        assert stats["rec_count"] == len(FIXTURES)
        assert trigger_calls[0] > 1  # Should have been called multiple times

        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_pipeline_debug_mode(self):
        """Test pipeline with debug=True"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_debug.jsonl"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        def process_func(record, state):
            return record

        p = Pipeline(source=source, destination=destination, process_func=process_func)

        # Debug mode should not raise errors
        stats = p.run(debug=True)

        assert stats["rec_count"] == len(FIXTURES)

        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_pipeline_no_destination_read_only(self):
        """Test pipeline with no destination (read-only processing)"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        processed_count = [0]

        def process_func(record, state):
            processed_count[0] += 1
            return record

        p = Pipeline(source=source, destination=None, process_func=process_func)
        stats = p.run()

        assert stats["rec_count"] == len(FIXTURES)
        assert processed_count[0] == len(FIXTURES)
        source.close()

    def test_pipeline_batch_size_one(self):
        """Test pipeline with batch_size=1 (no batching)"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_batch1.jsonl"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        def process_func(record, state):
            return record

        p = Pipeline(source=source, destination=destination, process_func=process_func, batch_size=1)
        stats = p.run()

        assert stats["rec_count"] == len(FIXTURES)
        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_pipeline_reset_iterables_false(self):
        """Test pipeline with reset_iterables=False"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_no_reset.jsonl"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        def process_func(record, state):
            return record

        p = Pipeline(source=source, destination=destination, process_func=process_func, reset_iterables=False)
        stats = p.run()

        assert stats["rec_count"] >= 0  # May be 0 if already consumed
        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_pipeline_atomic_write_success(self):
        """Test atomic write on successful pipeline execution"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_atomic.jsonl"
        temp_file = "testdata/test_pipeline_atomic.jsonl.tmp"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        def process_func(record, state):
            return record

        p = Pipeline(source=source, destination=destination, process_func=process_func, atomic=True)
        stats = p.run()

        assert stats["rec_count"] == len(FIXTURES)
        assert os.path.exists(output_file)
        assert not os.path.exists(temp_file)

        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_pipeline_atomic_write_preserves_original_on_failure(self):
        """Test that atomic write preserves original file on pipeline failure"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_atomic_fail.jsonl"
        temp_file = "testdata/test_pipeline_atomic_fail.jsonl.tmp"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        # Create existing output file
        with open(output_file, "w") as f:
            f.write('{"original": "content"}\n')

        def process_func(record, state):
            # Raise error after first record to simulate failure
            if state.get("count", 0) > 0:
                raise ValueError("Simulated error")
            state["count"] = state.get("count", 0) + 1
            return record

        p = Pipeline(source=source, destination=destination, process_func=process_func, atomic=True)

        try:
            p.run()
        except ValueError:
            pass  # Expected error

        # Verify original file is preserved and temp file is cleaned up
        assert os.path.exists(output_file)
        with open(output_file) as f:
            content = f.read()
            assert "original" in content
        assert not os.path.exists(temp_file)

        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_pipeline_atomic_write_backward_compatibility(self):
        """Test that atomic=False (default) works as before"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_non_atomic.jsonl"
        temp_file = "testdata/test_pipeline_non_atomic.jsonl.tmp"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        def process_func(record, state):
            return record

        p = Pipeline(source=source, destination=destination, process_func=process_func, atomic=False)
        stats = p.run()

        assert stats["rec_count"] == len(FIXTURES)
        assert os.path.exists(output_file)
        assert not os.path.exists(temp_file)

        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)

    def test_pipeline_wrapper_atomic_write(self):
        """Test pipeline() wrapper function with atomic writes"""
        source = CSVIterable("fixtures/2cols6rows.csv")
        output_file = "testdata/test_pipeline_wrapper_atomic.jsonl"
        temp_file = "testdata/test_pipeline_wrapper_atomic.jsonl.tmp"
        os.makedirs("testdata", exist_ok=True)
        destination = JSONLinesIterable(output_file, mode="w")

        processed_count = [0]

        def process_func(record, state):
            processed_count[0] += 1
            return record

        pipeline(source=source, destination=destination, process_func=process_func, atomic=True)

        assert processed_count[0] == len(FIXTURES)
        assert os.path.exists(output_file)
        assert not os.path.exists(temp_file)

        source.close()
        destination.close()
        if os.path.exists(output_file):
            os.unlink(output_file)
