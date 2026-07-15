## ADDED Requirements

### Requirement: No Silent Empty Reads

Datatype implementations SHALL NOT convert parse or dependency failures into empty result sets. When reading a malformed non-empty input under the default error policy (`on_error="raise"`), the implementation SHALL raise `FormatParseError` (or another `IterableDataError` subclass) rather than yielding zero records.

#### Scenario: Malformed file raises instead of reading empty

- **WHEN** a non-empty file that cannot be parsed by its format is read with default options
- **THEN** the implementation SHALL raise `FormatParseError` with the filename and format id in its context
- **AND** the implementation SHALL NOT return an iterator that yields zero records

#### Scenario: Skip policy tolerates bad records explicitly

- **WHEN** the user opens the same malformed input with `on_error="skip"`
- **THEN** unparseable records SHALL be skipped and valid records yielded
- **AND** skipped-record counts SHALL be available via the error-handling statistics

### Requirement: Centralized Error Policy Adoption

Datatype implementations that perform per-record parsing SHALL route record-level parse failures through the centralized `_handle_error()` mechanism so that `on_error="raise"|"skip"|"warn"` and error logging behave consistently across formats.

#### Scenario: Per-record failure honors on_error

- **WHEN** a record fails to parse in a format that supports record-level recovery
- **THEN** `on_error="raise"` SHALL raise `FormatParseError`
- **AND** `on_error="skip"` SHALL skip the record and continue
- **AND** `on_error="warn"` SHALL emit a warning and continue

### Requirement: Typed Errors at the API Boundary

`open_iterable()` and other public entry points SHALL raise `IterableDataError` subclasses (e.g. `ReadError`, `FormatDetectionError`, `FormatParseError`) for failures they surface, not bare `RuntimeError` or `ValueError`, so callers can catch library errors uniformly.

#### Scenario: Stream open failure is typed

- **WHEN** `open_iterable()` fails to open or detect a stream source
- **THEN** the raised exception SHALL be an `IterableDataError` subclass
- **AND** the message SHALL include the underlying cause

#### Scenario: Detection fallback is not silent

- **WHEN** stream format detection fails and no explicit format was given
- **THEN** the system SHALL NOT silently fall back to CSV
- **AND** it SHALL either raise a typed detection error or emit an explicit warning naming the assumed format
