## ADDED Requirements

### Requirement: Popular Format Throughput Workloads

The performance regression gate SHALL include read, write and conversion workloads for CSV, JSON Lines, JSON and Parquet at a representative size, and SHALL compare them with committed baselines.

#### Scenario: JSON Lines write regression

- **WHEN** a change makes the JSON Lines `write_bulk` workload slower than its baseline beyond the gate tolerance
- **THEN** the performance gate SHALL fail and name the workload

#### Scenario: Conversion pair coverage

- **WHEN** the gate runs
- **THEN** it SHALL measure CSV to JSON Lines, CSV to Parquet and JSON Lines to CSV conversions
