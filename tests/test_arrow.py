import os

import pytest
from fixdata import FIXTURES, FIXTURES_TYPES

pytest.importorskip("pyarrow", reason="pyarrow is required for Arrow support")

from iterable.datatypes import ArrowIterable  # noqa: E402

# Create fixture file if it doesn't exist
FIXTURE_FILE = "fixtures/2cols6rows.arrow"


def setup_module():
    """Create fixture file if it doesn't exist"""
    if not os.path.exists(FIXTURE_FILE):
        import pyarrow
        import pyarrow.feather

        table = pyarrow.Table.from_pylist(FIXTURES_TYPES)
        pyarrow.feather.write_feather(table, FIXTURE_FILE)


class TestArrow:
    def test_id(self):
        datatype_id = ArrowIterable.id()
        assert datatype_id == "arrow"

    def test_flatonly(self):
        flag = ArrowIterable.is_flatonly()
        assert flag

    def test_openclose(self):
        iterable = ArrowIterable(FIXTURE_FILE)
        iterable.close()

    def test_read_bulk_returns_n_records(self):
        iterable = ArrowIterable(FIXTURE_FILE)
        chunk = iterable.read_bulk(2)
        assert len(chunk) == 2
        assert chunk == FIXTURES_TYPES[:2]
        iterable.close()

    def test_parsesimple_readone(self):
        iterable = ArrowIterable(FIXTURE_FILE)
        row = iterable.read()
        assert row == FIXTURES_TYPES[0]
        iterable.close()

    def test_parsesimple_reset(self):
        iterable = ArrowIterable(FIXTURE_FILE)
        row = iterable.read()
        assert row == FIXTURES_TYPES[0]
        iterable.reset()
        row_reset = iterable.read()
        assert row_reset == FIXTURES_TYPES[0]
        iterable.close()

    def test_parsesimple_next(self):
        iterable = ArrowIterable(FIXTURE_FILE)
        row = next(iterable)
        assert row == FIXTURES_TYPES[0]
        iterable.reset()
        row_reset = next(iterable)
        assert row_reset == FIXTURES_TYPES[0]
        iterable.close()

    def test_parsesimple_count(self):
        iterable = ArrowIterable(FIXTURE_FILE)
        n = 0
        for _row in iterable:
            n += 1
        assert n == len(FIXTURES_TYPES)
        iterable.close()

    def test_parsesimple_iterateall(self):
        iterable = ArrowIterable(FIXTURE_FILE)
        n = 0
        for row in iterable:
            assert row == FIXTURES_TYPES[n]
            n += 1
        iterable.close()

    def test_write_read(self):
        iterable = ArrowIterable("testdata/2cols6rows_test.arrow", mode="w")
        iterable.write_bulk(FIXTURES)
        iterable.close()
        iterable = ArrowIterable("testdata/2cols6rows_test.arrow", mode="r")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_has_totals(self):
        iterable = ArrowIterable(FIXTURE_FILE)
        assert ArrowIterable.has_totals()
        total = iterable.totals()
        assert total == len(FIXTURES_TYPES)
        iterable.close()


class TestArrowStreaming:
    """Arrow IPC files must be read batch by batch in bounded memory."""

    ROWS = 200_000

    def _write_large(self, path):
        import pyarrow
        import pyarrow.ipc

        schema = pyarrow.schema([("id", pyarrow.int64()), ("name", pyarrow.string())])
        with pyarrow.ipc.new_file(path, schema) as writer:
            for start in range(0, self.ROWS, 10_000):
                batch = pyarrow.RecordBatch.from_pylist(
                    [{"id": i, "name": f"name-{i}-{'x' * 100}"} for i in range(start, start + 10_000)],
                    schema=schema,
                )
                writer.write_batch(batch)

    def test_is_streaming_for_ipc_files(self, tmp_path):
        path = str(tmp_path / "large.arrow")
        self._write_large(path)
        iterable = ArrowIterable(path)
        assert iterable.is_streaming()
        iterable.close()

    def test_large_read_bounded_memory(self, tmp_path):
        import tracemalloc

        path = str(tmp_path / "large.arrow")
        self._write_large(path)
        uncompressed_size = self.ROWS * 110

        iterable = ArrowIterable(path)
        tracemalloc.start()
        n = 0
        for row in iterable:
            assert row["id"] == n
            n += 1
        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        iterable.close()

        assert n == self.ROWS
        # Batch-wise reading keeps peak allocation far below the full payload.
        assert peak < uncompressed_size / 2, f"peak {peak} suggests full-table load"
