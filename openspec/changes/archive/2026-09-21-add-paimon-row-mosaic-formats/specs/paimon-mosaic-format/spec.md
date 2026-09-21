## ADDED Requirements

### Requirement: Paimon Mosaic Detection and Dependency

The system SHALL support Apache Paimon Mosaic files through an optional `paimon-mosaic` extra and SHALL detect them by `.mosaic` extension or, for seekable sources, by a valid trailing footer whose magic is `MOSA` (`0x4D4F5341`).

#### Scenario: Open by extension

- **WHEN** a user opens a path ending in `.mosaic` through `open_iterable()`
- **THEN** the Paimon Mosaic iterable SHALL be selected

#### Scenario: Open by footer magic

- **WHEN** a seekable file has a valid 32-byte Mosaic footer ending in `MOSA`
- **THEN** content detection SHALL select the Paimon Mosaic format even without a `.mosaic` extension

#### Scenario: Missing dependency

- **WHEN** Mosaic support is requested without the required package installed
- **THEN** an `ImportError` SHALL name the `paimon-mosaic` installation extra

### Requirement: Bounded Mosaic Row Iteration

The system SHALL read Mosaic files by row group using the official Python bindings, convert Arrow record batches to dictionary rows, and SHALL apply column projection through the Mosaic reader when `columns` (or equivalent) is requested so only relevant buckets are decompressed.

#### Scenario: Stream row groups

- **WHEN** a valid Mosaic file is opened for reading
- **THEN** iteration SHALL yield dictionary records without requiring a whole-file `read_all()` on the hot path

#### Scenario: Projection pushdown

- **WHEN** a column projection is requested
- **THEN** the backend projection API SHALL be used before row-group materialization
- **AND** yielded rows SHALL contain only the projected columns in the requested order

#### Scenario: Totals from metadata

- **WHEN** `totals()` is called on a Mosaic file
- **THEN** it SHALL return the total row count from Mosaic metadata/row-group sums without decoding every value column when possible

### Requirement: Mosaic Writing and Round Trip

The system SHALL write Mosaic files via the official writer API from dictionary or bulk records (converted through PyArrow) and SHALL round-trip supported field values and schema.

#### Scenario: Write and re-read

- **WHEN** supported records are written to a `.mosaic` file and reopened
- **THEN** the logical field values SHALL match the written data for supported types

#### Scenario: Writer options

- **WHEN** Mosaic writer options such as bucket count or compression are supplied in `iterableargs`
- **THEN** they SHALL be forwarded to the underlying `WriterOptions` where supported
- **AND** invalid combinations SHALL fail with a clear error

#### Scenario: Bulk operations

- **WHEN** `read_bulk()` or `write_bulk()` is used
- **THEN** multiple rows SHALL be processed per call according to the standard IterableData bulk contract
