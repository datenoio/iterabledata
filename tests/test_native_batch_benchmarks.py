"""Throughput and peak-memory benchmarks for columnar-to-columnar conversion.

Compares the opt-in native batch path against the row/bulk fallback for
Parquet->Parquet, ORC->Parquet, and Parquet->Arrow conversions.

Run with: pytest tests/test_native_batch_benchmarks.py -m benchmark --benchmark-only
Peak-memory numbers are printed with `-s` (tracemalloc peak per run).
"""

import datetime
import tracemalloc

import pytest

pytest.importorskip("pytest_benchmark", reason="pytest-benchmark not installed (pip install pytest-benchmark)")
pyarrow = pytest.importorskip("pyarrow")
pyarrow_parquet = pytest.importorskip("pyarrow.parquet")

from iterable.convert import BatchSelection, convert  # noqa: E402
from iterable.datatypes.orc import HAS_PYARROW_ORC, ORCIterable  # noqa: E402

# Excluded from the default run via addopts; run with: pytest -m benchmark
pytestmark = pytest.mark.benchmark

NUM_ROWS = 50000


def _rows(count):
    day0 = datetime.date(2024, 1, 1)
    return [
        {
            "id": i,
            "name": f"person{i % 1000}",
            "value": None if i % 7 == 0 else i * 1.25,
            "score": (i % 100) / 100.0,
            "day": day0 + datetime.timedelta(days=i % 365),
            "category": f"cat{i % 10}",
        }
        for i in range(count)
    ]


@pytest.fixture(scope="module")
def parquet_source(tmp_path_factory):
    path = tmp_path_factory.mktemp("bench") / "source.parquet"
    pyarrow_parquet.write_table(pyarrow.Table.from_pylist(_rows(NUM_ROWS)), path)
    return str(path)


@pytest.fixture(scope="module")
def orc_source(tmp_path_factory):
    if not HAS_PYARROW_ORC:
        pytest.skip("pyarrow.orc backend not available")
    path = str(tmp_path_factory.mktemp("bench") / "source.orc")
    writer = ORCIterable(path, mode="w", backend="pyarrow")
    writer.write_bulk(_rows(NUM_ROWS))
    writer.close()
    return path


def _force_row_fallback(monkeypatch):
    monkeypatch.setattr("iterable.convert.core.native_batch_supported", lambda reader, writer: False)


def _convert_peak_memory(callable_):
    """Run a conversion once under tracemalloc and return the peak bytes."""
    tracemalloc.start()
    try:
        callable_()
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak


class TestParquetToParquetBenchmarks:
    """Columnar-to-columnar: Parquet source, Parquet destination."""

    def test_row_path(self, benchmark, tmp_path, parquet_source, monkeypatch):
        _force_row_fallback(monkeypatch)
        dst = tmp_path / "out.parquet"
        result = benchmark(convert, parquet_source, str(dst), use_native_batch=True)
        assert result.rows_out == NUM_ROWS

    def test_native_path(self, benchmark, tmp_path, parquet_source):
        dst = tmp_path / "out.parquet"
        result = benchmark(convert, parquet_source, str(dst), use_native_batch=True)
        assert result.rows_out == NUM_ROWS

    def test_native_path_with_pushdown(self, benchmark, tmp_path, parquet_source):
        dst = tmp_path / "out.parquet"
        selection = BatchSelection(columns=("id", "value"), predicate=("id", ">=", 100))
        result = benchmark(convert, parquet_source, str(dst), use_native_batch=True, selection=selection)
        assert result.rows_out == NUM_ROWS - 100

    def test_peak_memory_row_path(self, benchmark, tmp_path, parquet_source, monkeypatch):
        _force_row_fallback(monkeypatch)
        dst = tmp_path / "out.parquet"
        peak = benchmark.pedantic(
            lambda: _convert_peak_memory(lambda: convert(parquet_source, str(dst), use_native_batch=True)),
            rounds=1,
            iterations=1,
        )
        print(f"\nparquet->parquet row path peak memory: {peak / 1e6:.1f} MB")
        assert peak > 0

    def test_peak_memory_native_path(self, benchmark, tmp_path, parquet_source):
        dst = tmp_path / "out.parquet"
        peak = benchmark.pedantic(
            lambda: _convert_peak_memory(lambda: convert(parquet_source, str(dst), use_native_batch=True)),
            rounds=1,
            iterations=1,
        )
        print(f"\nparquet->parquet native path peak memory: {peak / 1e6:.1f} MB")
        assert peak > 0


class TestORCToParquetBenchmarks:
    """Columnar-to-columnar: ORC (pyarrow backend) source, Parquet destination."""

    def test_row_path(self, benchmark, tmp_path, orc_source, monkeypatch):
        _force_row_fallback(monkeypatch)
        dst = tmp_path / "out.parquet"
        args = {"backend": "pyarrow"}
        result = benchmark(convert, str(orc_source), str(dst), iterableargs=args, use_native_batch=True)
        assert result.rows_out == NUM_ROWS

    def test_native_path(self, benchmark, tmp_path, orc_source):
        dst = tmp_path / "out.parquet"
        args = {"backend": "pyarrow"}
        result = benchmark(convert, str(orc_source), str(dst), iterableargs=args, use_native_batch=True)
        assert result.rows_out == NUM_ROWS


class TestParquetToArrowBenchmarks:
    """Columnar-to-columnar: Parquet source, Arrow IPC destination."""

    def test_row_path(self, benchmark, tmp_path, parquet_source, monkeypatch):
        _force_row_fallback(monkeypatch)
        dst = tmp_path / "out.arrow"
        result = benchmark(convert, parquet_source, str(dst), use_native_batch=True)
        assert result.rows_out == NUM_ROWS

    def test_native_path(self, benchmark, tmp_path, parquet_source):
        dst = tmp_path / "out.arrow"
        result = benchmark(convert, parquet_source, str(dst), use_native_batch=True)
        assert result.rows_out == NUM_ROWS
