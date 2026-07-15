# Change: Make the test suite resilient to missing optional dependencies

## Why

Running the suite in a base environment (no pyarrow/duckdb/dbfread/warcio/lxml/python-snappy) produces 19 collection errors and ~60 import-related failures instead of clean skips, because test modules import optional classes at module top level (e.g. `from iterable.datatypes import ParquetIterable`) without `importorskip`. Separately, the committed `tests/testdata` symlink can materialize as a plain file on checkouts with `core.symlinks=false`, causing ~150 spurious `FileExistsError`/`NotADirectoryError` failures, and the global 300 s `pytest-timeout` is tripped by the 10 GB streaming stress test, aborting the default `pytest --verbose` run mid-suite. Stale tests also remain after recent refactors (`test_benchmarks.py` uses the old `read_bulk` chunk-generator contract; `test_ai_plan.py::test_plan_readonly_target_warning` predates Avro write support).

## What Changes

- Convert top-level optional imports in test modules to `pytest.importorskip` or module-level skip guards so missing extras skip rather than error at collection.
- Add a conftest guard that fails fast with a clear message when `tests/testdata` is not a symlink to `tests/fixtures`.
- Give stress/slow tests their own per-test timeouts and exclude `stress`/`slow`/`benchmark`/`integration` from default `addopts`, so the documented default run passes.
- Update stale tests: `test_benchmarks.py` for the single-list `read_bulk` contract, and `test_ai_plan.py::test_plan_readonly_target_warning` for Avro being writable.
- Add a minimal CI job that runs the suite with no optional extras and asserts zero collection errors.

## Impact

- Affected specs: `test-suite` (new capability)
- Affected code: `tests/conftest.py`, `tests/test_parquet.py`, `test_orc.py`, `test_dbf.py`, `test_duckdb*.py`, `test_totals.py`, `test_warc.py`, `test_html.py`, `test_arrow.py`, `test_snappy.py`, `test_detect.py`, `test_benchmarks.py`, `test_ai_plan.py`, `pyproject.toml` addopts, `.github/workflows/`
- No product code change; improves test reliability and honesty across environments.
