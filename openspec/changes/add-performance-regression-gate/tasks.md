## 1. Baselines

- [x] 1.1 Define representative workloads (CSV read, JSONL read, compressed JSONL→Parquet convert, bulk read/write)
- [x] 1.2 Generate and commit `tests/performance_baselines.json` on a documented reference environment
- [x] 1.3 Document the regeneration procedure

## 2. Activate the gate

- [x] 2.1 Update `test_performance_regression.py` to load the committed baselines and compare with an explicit tolerance
- [x] 2.2 Fail only on regressions beyond tolerance; skip gracefully if a workload's optional deps are missing

## 3. CI wiring

- [x] 3.1 Move `@pytest.mark.benchmark` tests out of the default matrix into a dedicated job
- [x] 3.2 Add a single-leg CI job (one OS/Python) that runs the regression gate
- [x] 3.3 Tune tolerances/warmup to avoid flakiness

## 4. Verify

- [x] 4.1 Confirm the gate passes on an unchanged tree and fails on an injected slowdown
- [x] 4.2 Lint
