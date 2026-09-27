## ADDED Requirements

### Requirement: Committed Fixtures Are Immutable Test Inputs

Tests SHALL NOT create, rewrite, or normalize output directly in tracked fixture paths. Write and round-trip tests SHALL use temporary paths or copies, and CI SHALL fail if the test run modifies tracked fixtures.

#### Scenario: Binary round-trip test

- **WHEN** a test writes Avro, DBF, gzip, or another binary format
- **THEN** its output SHALL be under `tmp_path` or another temporary directory
- **AND** the committed source fixture SHALL remain byte-identical

#### Scenario: Full test run completes

- **WHEN** the default and representative-extra test jobs finish
- **THEN** `git diff --exit-code -- tests/fixtures` SHALL succeed
- **AND** any fixture mutation SHALL fail the job with the changed paths

### Requirement: Layered Dependency Test Environments

CI SHALL separately test a minimal installation, cross-platform core development environments, and representative optional-dependency families. Missing optional dependencies SHALL not make all tests for an advertised format skip across every CI job.

#### Scenario: Minimal environment

- **WHEN** the package is installed without optional format extras
- **THEN** imports and core CSV/JSONL smoke tests SHALL pass
- **AND** optional tests SHALL skip cleanly with reasons

#### Scenario: Representative format family

- **WHEN** a family job installs its declared extras
- **THEN** the corresponding format tests SHALL execute rather than skip for missing dependencies
- **AND** failures SHALL identify the owning format family

### Requirement: Risk-Weighted Coverage Reporting

Core and representative-extra jobs SHALL report coverage for the code they exercise, and reviewed staged floors SHALL increase without relying only on one global aggregate.

#### Scenario: Optional family job completes

- **WHEN** a geospatial, lakehouse, database, or other family job runs
- **THEN** its coverage report SHALL expose the relevant package/module coverage
- **AND** the configured family floor SHALL be evaluated

#### Scenario: Coverage floor changes

- **WHEN** maintainers raise a floor
- **THEN** the new value SHALL be intentional and documented
- **AND** tests added to reach it SHALL assert behavior, errors, and resource handling rather than only execute lines
