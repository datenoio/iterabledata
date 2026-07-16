"""Regression tests for shared batch cursors and bounded columnar writes."""

import tracemalloc

import pytest

pyarrow = pytest.importorskip("pyarrow")

from iterable.datatypes.arrow import ArrowIterable  # noqa: E402
from iterable.datatypes.csv import CSVIterable  # noqa: E402
from iterable.datatypes.jsonl import JSONLinesIterable  # noqa: E402
from iterable.datatypes.parquet import ParquetIterable  # noqa: E402

ROWS = [{"id": index, "value": f"row-{index}"} for index in range(5)]


def test_parquet_read_and_bulk_share_one_cursor(tmp_path):
    path = tmp_path / "rows.parquet"
    with ParquetIterable(str(path), mode="w", batch_size=2) as output:
        for row in ROWS:
            output.write(row)

    with ParquetIterable(str(path), batch_size=2) as source:
        assert source.read() == ROWS[0]
        assert source.read_bulk(2) == ROWS[1:3]
        assert source.read_bulk(10) == ROWS[3:]

    metadata = pyarrow.parquet.ParquetFile(path).metadata
    assert metadata.num_rows == len(ROWS)
    assert metadata.num_row_groups <= 3


def test_arrow_read_and_bulk_share_one_cursor(tmp_path):
    path = tmp_path / "rows.arrow"
    with ArrowIterable(str(path), mode="w", batch_size=2) as output:
        for row in ROWS:
            output.write(row)

    with ArrowIterable(str(path), batch_size=2) as source:
        assert source.read() == ROWS[0]
        assert source.read_bulk(2) == ROWS[1:3]
        assert source.read_bulk(10) == ROWS[3:]


@pytest.mark.parametrize("datatype, suffix", [(CSVIterable, ".csv"), (JSONLinesIterable, ".jsonl")])
def test_text_row_and_bulk_paths_are_equivalent(tmp_path, datatype, suffix):
    path = tmp_path / f"rows{suffix}"
    kwargs = {"keys": ["id", "value"]} if datatype is CSVIterable else {}
    with datatype(str(path), mode="w", **kwargs) as output:
        output.write_bulk(ROWS)
    with datatype(str(path), **kwargs) as row_source:
        row_rows = list(row_source)
    with datatype(str(path), **kwargs) as bulk_source:
        bulk_rows = bulk_source.read_bulk(100)
    assert row_rows == bulk_rows


def test_parquet_write_buffer_has_bounded_peak_memory(tmp_path):
    path = tmp_path / "bounded.parquet"
    tracemalloc.start()
    with ParquetIterable(str(path), mode="w", batch_size=128) as output:
        for index in range(512):
            output.write({"id": index, "value": "x" * 32})
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert peak < 32 * 1024 * 1024
