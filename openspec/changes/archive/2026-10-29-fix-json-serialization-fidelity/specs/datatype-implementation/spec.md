## ADDED Requirements

### Requirement: Lossless JSON Value Serialization

Every JSON-family writer SHALL serialize record values through one shared encoder and SHALL NOT write `null` for a value that is not `None`. Values without a lossless JSON form SHALL use the documented textual encoding; other objects SHALL be written as `str(value)`, or raise `WriteError` when `on_unknown_type="raise"`.

#### Scenario: Time and decimal values written to JSON Lines

- **WHEN** a record containing `datetime.time(12, 30)` and `Decimal("1.50")` is written to a `.jsonl` file
- **THEN** the line SHALL contain `"12:30:00"` for the time value
- **AND** the decimal SHALL be written as the JSON number `1.5`

#### Scenario: Decimal that a float cannot represent

- **WHEN** a record contains `Decimal("12345678901234567890.123456789")`
- **THEN** the writer SHALL write it as the string `"12345678901234567890.123456789"`
- **AND** it SHALL NOT round the value

#### Scenario: JSON and JSON Lines writers agree

- **WHEN** the same record is written once to `.json` and once to `.jsonl`
- **THEN** each field SHALL have the same JSON value in both outputs

#### Scenario: Unsupported value type

- **WHEN** a record contains an object with no documented encoding and `on_unknown_type` is not set
- **THEN** the writer SHALL write `str(value)` for that field
- **AND** with `on_unknown_type="raise"` it SHALL raise `WriteError` naming the Python type and write no partial line

### Requirement: Size-Independent JSON Decoding

The JSON array reader SHALL return the same Python value types for a document regardless of whether it is parsed in memory or streamed.

#### Scenario: Large JSON array with floats

- **WHEN** a JSON array larger than the streaming threshold contains the number `0.5`
- **THEN** the reader SHALL return it as a `float`
- **AND** converting the file to JSON Lines SHALL write `0.5`
