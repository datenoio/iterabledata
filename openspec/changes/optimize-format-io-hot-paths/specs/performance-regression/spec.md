## ADDED Requirements

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
