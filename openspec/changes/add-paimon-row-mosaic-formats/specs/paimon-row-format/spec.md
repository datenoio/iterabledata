## ADDED Requirements

### Requirement: Paimon Row Detection and Dependency

The system SHALL support Apache Paimon Row (`.row`) files through an optional `paimon-row` extra and SHALL detect them by `.row` extension or, for seekable sources, by a valid trailing footer whose magic is `ROWS` (`0x524F5753`).

#### Scenario: Open by extension

- **WHEN** a user opens a path ending in `.row` through `open_iterable()`
- **THEN** the Paimon Row iterable SHALL be selected

#### Scenario: Open by footer magic

- **WHEN** a seekable file has a valid 32-byte Paimon Row footer ending in `ROWS`
- **THEN** content detection SHALL select the Paimon Row format even without a `.row` extension

#### Scenario: Missing dependency

- **WHEN** Paimon Row support is requested without the required package installed
- **THEN** an `ImportError` SHALL name the `paimon-row` installation extra

### Requirement: Schema-Required Paimon Row Reading

Because Paimon Row files do not embed schema, the system SHALL require an explicit schema for reads and SHALL yield dictionary records whose keys follow that schema in physical field order.

#### Scenario: Read with schema

- **WHEN** a valid `.row` file is opened with a supported schema in `iterableargs`
- **THEN** iteration SHALL yield one dictionary per row without loading the entire file into memory beyond the active block/batch

#### Scenario: Missing schema

- **WHEN** a `.row` file is opened for reading without a schema
- **THEN** the system SHALL raise a clear error naming the required schema argument

#### Scenario: Totals from footer

- **WHEN** `totals()` is called on a valid Paimon Row file
- **THEN** it SHALL return `totalRowCount` from the footer without a full row decode when the footer is readable

### Requirement: Paimon Row Writing and Round Trip

The system SHALL write Paimon Row files that conform to the published block/index/footer layout and SHALL round-trip supported primitive field values when the same schema is supplied on read.

#### Scenario: Write and re-read

- **WHEN** supported records are written to a `.row` file and reopened with the same schema
- **THEN** the logical field values SHALL match the written data

#### Scenario: Bounded block flush

- **WHEN** records are written with the default or configured block size
- **THEN** the writer SHALL flush compressed blocks incrementally rather than retaining the entire output until close when the backend allows

#### Scenario: Bulk operations

- **WHEN** `read_bulk()` or `write_bulk()` is used
- **THEN** multiple rows SHALL be processed per call according to the standard IterableData bulk contract
