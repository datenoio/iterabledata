## ADDED Requirements

### Requirement: Backend-Independent JSON Output

JSON and JSON Lines readers and writers SHALL use an accelerated JSON backend when it is installed and the standard library otherwise. Returned records SHALL be identical for both backends, and written bytes SHALL be identical except for floats below `1e-4`, which may be written in positional or exponent form with the same value.

#### Scenario: Same output with and without orjson

- **WHEN** the same records, without floats below `1e-4`, are written to JSON Lines once with `orjson` installed and once with the standard-library backend forced
- **THEN** the two files SHALL be byte-identical

#### Scenario: Input the accelerated parser rejects

- **WHEN** a JSON Lines record contains a literal the accelerated parser rejects but the standard library accepts (for example `NaN`)
- **THEN** the reader SHALL return the standard library's result for that line
- **AND** it SHALL NOT raise `FormatParseError`

#### Scenario: Integers beyond 64 bits

- **WHEN** a JSON Lines record contains an integer literal beyond the 64-bit range
- **THEN** the reader SHALL return the exact integer, not a float

### Requirement: CSV Fast Path Preserves Record Semantics

The CSV reader and writer SHALL return and accept the same records as `csv.DictReader` and `csv.DictWriter` with the configured dialect, including rows shorter or longer than the header.

#### Scenario: Short row

- **WHEN** a data row has fewer fields than the header
- **THEN** the missing fields SHALL be `None`

#### Scenario: Long row

- **WHEN** a data row has more fields than the header
- **THEN** the extra values SHALL be returned as a list under the `None` key

### Requirement: Single Conversion per Parquet Batch

The Parquet writer SHALL convert each written batch to Arrow once and SHALL reuse that conversion for schema validation and output.

#### Scenario: Bulk write after the schema is fixed

- **WHEN** `write_bulk()` is called after the writer schema exists
- **THEN** the batch SHALL be converted to an Arrow table or record batch once
- **AND** a schema mismatch SHALL still raise `WriteError` for that batch
