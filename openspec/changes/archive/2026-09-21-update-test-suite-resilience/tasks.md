## 1. Optional-dependency skips

- [x] 1.1 Replace top-level optional imports with `pytest.importorskip` (or module `HAS_*` skip guards) in `test_parquet.py`, `test_orc.py`, `test_dbf.py`, `test_duckdb.py`, `test_duckdb_format.py`, `test_totals.py`, `test_warc.py`, `test_html.py`, `test_arrow.py`, `test_snappy.py`, `test_detect.py`, `tests/extra/extra_parquet.py`
- [x] 1.2 Verify a base-env run reports 0 collection errors

## 2. Fixture symlink guard

- [x] 2.1 Add a `conftest.py` check that raises a clear error if `tests/testdata` is not a symlink pointing at `fixtures`
- [x] 2.2 Document the requirement (checkout with symlinks enabled) in the testing docs/AGENTS

## 3. Timeouts and default markers

- [x] 3.1 Add per-test `@pytest.mark.timeout(...)` to the 10 GB stress tests
- [x] 3.2 Exclude `stress`/`slow`/`benchmark`/`integration` from default `addopts` in `pyproject.toml`

## 4. Stale tests

- [x] 4.1 Fix `test_benchmarks.py` to the single-list `read_bulk()` contract
- [x] 4.2 Fix `test_ai_plan.py::test_plan_readonly_target_warning` for Avro being writable

## 5. CI

- [x] 5.1 Add a no-extras CI job asserting zero collection errors and a green base-env run
- [x] 5.2 Run the full suite locally and confirm the default invocation passes
