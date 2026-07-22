## ADDED Requirements

### Requirement: Paimon Table Detection and Dependency

The system SHALL support Apache Paimon **tables** through an optional `paimon-table` extra and canonical format id `paimon`, distinct from standalone `paimon_row` and `paimon_mosaic` file formats.

#### Scenario: Explicit table open

- **WHEN** a user opens a warehouse/catalog with `format="paimon"` and table coordinates
- **THEN** the Paimon table iterable SHALL be selected

#### Scenario: File formats remain unchanged

- **WHEN** a user opens a `.row` or `.mosaic` path without `format="paimon"`
- **THEN** the existing file iterables SHALL remain selected

#### Scenario: Missing dependency

- **WHEN** Paimon table support is requested without PyPaimon installed
- **THEN** an `ImportError` SHALL name the `paimon-table` (or convenience `paimon`) installation extra

### Requirement: Paimon Table Discovery and Selection

The iterable SHALL require database/table identity and SHALL expose discoverable tables through `list_tables()` using a documented naming scheme.

#### Scenario: List tables

- **WHEN** `list_tables()` is called on a readable Paimon warehouse/catalog
- **THEN** it SHALL return discoverable table identifiers in deterministic order

#### Scenario: Missing table coordinates

- **WHEN** `format="paimon"` is used without required database/table options
- **THEN** the system SHALL raise a clear selection error

### Requirement: Bounded Paimon Table Reading

Paimon tables SHALL be read through PyPaimon read APIs with peak memory bounded by batch size, yielding dictionary rows, and SHOULD honor projection options when requested.

#### Scenario: Stream rows

- **WHEN** a Paimon table is opened for reading
- **THEN** iteration SHALL yield dictionary records without requiring a full in-memory table materialization when PyPaimon provides an incremental API

#### Scenario: Projection

- **WHEN** a column projection is requested and supported
- **THEN** yielded rows SHALL contain only the projected columns

### Requirement: Paimon Table Writing

The system SHALL support documented write modes (at least append for supported table kinds) via PyPaimon write/commit builders with bounded batch flushing, and SHALL fail clearly for unsupported modes.

#### Scenario: Append round trip

- **WHEN** supported records are appended and committed to a writable Paimon table and the table is re-read
- **THEN** the new rows SHALL be visible according to commit semantics

#### Scenario: Unsupported write mode

- **WHEN** an unsupported write mode or table kind is requested
- **THEN** the system SHALL raise a clear error without partially committing silent data corruption
