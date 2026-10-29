# performance-regression Specification

## Purpose
TBD - created by archiving change add-performance-regression-gate. Update Purpose after archive.
## Requirements
### Requirement: Enforced Performance Regression Gate

The project SHALL maintain committed performance baselines and a regression test that compares representative workloads against those baselines within an explicit tolerance, failing when a meaningful regression is detected. The gate SHALL run in CI on at least one environment.

#### Scenario: Regression fails the gate

- **WHEN** a representative workload runs measurably slower than its committed baseline beyond the configured tolerance
- **THEN** the regression test SHALL fail
- **AND** the failure message SHALL report the workload, baseline, and observed measurement

#### Scenario: Within tolerance passes

- **WHEN** a workload runs within the configured tolerance of its baseline
- **THEN** the regression test SHALL pass

#### Scenario: Missing baseline is not a silent skip in CI

- **WHEN** the regression gate runs in CI and a baseline file is absent
- **THEN** the gate SHALL fail rather than skip
- **AND** the message SHALL instruct how to generate baselines

### Requirement: Benchmarks Separated From Default Matrix

Benchmark-marked tests SHALL run in a dedicated CI job rather than the default test matrix, so the default run stays fast and benchmark timing noise does not gate ordinary changes.

#### Scenario: Default matrix excludes benchmarks

- **WHEN** the default test matrix runs
- **THEN** `@pytest.mark.benchmark` tests SHALL NOT execute
- **AND** they SHALL execute in their dedicated job instead

### Requirement: Paired API Path Regression Checks

The performance suite SHALL compare semantically equivalent row and bulk paths for representative streaming and columnar formats on the same runner, and SHALL fail when an optimized bulk path regresses beyond its declared ratio tolerance.

#### Scenario: JSONL bulk path is not slower than row iteration

- **WHEN** representative 10,000-row and 100,000-row JSONL workloads are measured
- **THEN** `read_bulk(1000)` SHALL complete within the configured narrow ratio of row iteration
- **AND** the failure SHALL report both measurements and their ratio

#### Scenario: Columnar bulk path remains efficient

- **WHEN** Parquet and Arrow row and bulk reads are measured on identical fixtures
- **THEN** the bulk path SHALL remain within its committed paired-path tolerance
- **AND** both paths SHALL return the same ordered records

### Requirement: Structural and Memory Performance Gates

Performance regression tests SHALL protect bounded memory and important physical output structure in addition to elapsed time.

#### Scenario: Parquet row-group structure

- **WHEN** a representative dataset is written through repeated Parquet `write()` calls
- **THEN** the row-group count SHALL remain proportional to the configured row-group target
- **AND** the test SHALL fail if normal row writes produce one row group per record

#### Scenario: Bounded writer memory

- **WHEN** a writer declared as bounded processes input larger than several configured batches
- **THEN** peak retained memory SHALL stay within the documented allowance
- **AND** the test SHALL report the format, batch size, and observed peak on failure

### Requirement: Lightweight Package Import

Importing the top-level `iterable` package SHALL NOT import optional database drivers, columnar or dataframe libraries, HTTP clients or terminal UI libraries. Such backends SHALL be imported on first use.

#### Scenario: Plain package import

- **WHEN** a fresh interpreter runs `import iterable` with all optional extras installed
- **THEN** none of `elasticsearch`, `pymongo`, `pyarrow`, `numpy`, `pandas`, `duckdb`, `httpx` or `rich` SHALL be present in `sys.modules`

#### Scenario: Database driver on demand

- **WHEN** a user opens a `postgres://` source after importing `iterable`
- **THEN** only the PostgreSQL driver module SHALL be imported to serve the request

#### Scenario: Import-time regression

- **WHEN** the performance regression gate runs
- **THEN** the measured `import iterable` time SHALL be compared with its committed baseline like other workloads

