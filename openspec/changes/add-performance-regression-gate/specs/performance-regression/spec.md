## ADDED Requirements

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
