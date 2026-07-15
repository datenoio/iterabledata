# Change: Add an enforced performance regression gate

## Why

`tests/test_performance_regression.py` exists but is inert: `tests/performance_baselines.json` is not committed, so every regression test calls `pytest.skip("No baseline available...")`. There is no enforced performance gate in CI, so streaming/memory regressions (the library's core value) can land unnoticed. The review also found `test_benchmarks.py` running in the default matrix, which slows CI without gating anything.

## What Changes

- Commit a `tests/performance_baselines.json` with baselines for a small set of representative workloads (CSV read, JSONL read, compressed JSONL → Parquet convert, bulk read/write throughput).
- Activate `test_performance_regression.py` to compare against the committed baselines with an explicit tolerance, failing only on meaningful regressions.
- Move `@pytest.mark.benchmark` tests out of the default matrix into a dedicated CI job.
- Add a single CI leg (one OS/Python) that runs the regression gate and publishes results; keep it non-flaky via generous tolerances and warmup.
- Document how to regenerate baselines intentionally when a change legitimately alters performance.

## Impact

- Affected specs: `performance-regression` (new capability)
- Affected code: `tests/performance_baselines.json` (new), `tests/test_performance_regression.py`, `pyproject.toml` markers/addopts, `.github/workflows/`
- No product code change; adds a safety net for the streaming/memory guarantees.
