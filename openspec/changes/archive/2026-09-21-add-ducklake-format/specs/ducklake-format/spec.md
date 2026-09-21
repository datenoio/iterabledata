## ADDED Requirements

### Requirement: DuckLake Detection and Dependency

The system SHALL support DuckLake tables through an optional `ducklake` extra and SHALL select the DuckLake iterable when `format="ducklake"` is provided or when a documented DuckLake catalog path/URI is recognized, without classifying ordinary DuckDB database files as DuckLake by extension alone.

#### Scenario: Explicit format open

- **WHEN** a user opens a DuckLake catalog with `iterableargs` including `format="ducklake"` and a table identifier
- **THEN** the DuckLake iterable SHALL be selected

#### Scenario: Missing dependency

- **WHEN** DuckLake support is requested without the required package installed
- **THEN** an `ImportError` SHALL name the `ducklake` installation extra

#### Scenario: Ordinary DuckDB file

- **WHEN** a path ending in `.duckdb` is opened without DuckLake format selection or DuckLake metadata
- **THEN** it SHALL NOT be silently treated as a DuckLake catalog

### Requirement: DuckLake Table Discovery and Selection

The iterable SHALL expose catalog tables through `list_tables()` and SHALL require deterministic table selection when more than one table could be read.

#### Scenario: List tables

- **WHEN** `list_tables()` is called on an open DuckLake catalog
- **THEN** it SHALL return discoverable table names in deterministic order

#### Scenario: Ambiguous catalog

- **WHEN** a catalog contains multiple tables and no table option is supplied
- **THEN** the iterable SHALL raise a clear selection error naming available tables

### Requirement: Bounded DuckLake Row Iteration

DuckLake tables SHALL be read through backend scans/batch readers with peak memory bounded by batch size, yielding dictionary records consistent with other lakehouse iterables.

#### Scenario: Stream batches

- **WHEN** a DuckLake table is opened for reading
- **THEN** iteration SHALL yield dictionary rows without materializing the full table when the SDK provides a batch reader

#### Scenario: Totals

- **WHEN** `totals()` is called on a readable DuckLake table
- **THEN** it SHALL return the row count from SDK metadata or a count scan without retaining all rows in memory

### Requirement: DuckLake Writing When Supported

When the pinned DuckLake SDK exposes stable append/create APIs, the system SHALL support bounded writes of dictionary records into a DuckLake table; otherwise the descriptor SHALL declare the format non-writable and attempts to write SHALL raise `WriteNotSupportedError`.

#### Scenario: Append round trip

- **WHEN** supported records are appended to a DuckLake table and the table is reopened
- **THEN** the logical field values SHALL be present in subsequent reads for supported types

#### Scenario: Unsupported write SDK

- **WHEN** the chosen SDK cannot write and write mode is requested
- **THEN** the system SHALL raise `WriteNotSupportedError` with a clear message
