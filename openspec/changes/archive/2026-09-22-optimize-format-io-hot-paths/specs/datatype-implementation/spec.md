## ADDED Requirements

### Requirement: Unified Row and Bulk Cursor Semantics

Every datatype that implements both `read()` and `read_bulk()` SHALL advance one logical cursor. Any interleaving of the two methods SHALL yield each source record exactly once and in source order, unless the user explicitly calls `reset()`.

#### Scenario: Row read followed by bulk read

- **WHEN** a user reads one record with `read()` and then calls `read_bulk(2)`
- **THEN** the bulk result SHALL contain the next two records
- **AND** it SHALL NOT repeat the record returned by `read()`

#### Scenario: Bulk read followed by row read

- **WHEN** a user calls `read_bulk(n)` and then calls `read()`
- **THEN** `read()` SHALL return the record immediately following the bulk result
- **AND** no record SHALL be skipped

#### Scenario: Reset restores the initial cursor

- **WHEN** row and bulk reads have advanced the iterable and the user calls `reset()`
- **THEN** the next read SHALL return the first record again
- **AND** all backend and remainder cursor state SHALL be cleared

### Requirement: Bounded Incremental Writers

Writable formats that declare bounded write memory SHALL flush records at a configurable batch or row-group boundary and SHALL NOT retain the complete output dataset until close. Formats whose backend cannot append incrementally SHALL declare whole-output memory behavior explicitly.

#### Scenario: Parquet row writes form bounded row groups

- **WHEN** records are supplied one at a time to a Parquet writer
- **THEN** records SHALL be accumulated into bounded row groups
- **AND** writer creation SHALL NOT cause each later record to become its own row group

#### Scenario: Arrow or Lance writes exceed one batch

- **WHEN** more records than the configured write batch size are written to Arrow or Lance
- **THEN** completed batches SHALL be flushed incrementally
- **AND** peak retained records SHALL remain proportional to the configured batch size

#### Scenario: Backend requires whole-output buffering

- **WHEN** a format backend cannot safely append or stream its output
- **THEN** the implementation SHALL declare whole-output write memory behavior
- **AND** the format documentation SHALL state the limitation

### Requirement: Low-Overhead Success Paths

Streaming text readers SHALL preserve actionable parse-error context without performing avoidable seek/tell or equivalent decoder-position work for every valid record.

#### Scenario: JSONL bulk read of valid input

- **WHEN** a valid JSONL file is read with `read_bulk()`
- **THEN** the reader SHALL parse lines incrementally without a successful `tell()` call per line
- **AND** line numbers SHALL remain available for any later parse error

#### Scenario: Malformed text record

- **WHEN** a text record cannot be parsed
- **THEN** the raised error SHALL include the format, filename when available, and record or line number
- **AND** byte offset MAY be omitted when the active stream cannot provide it cheaply or correctly
