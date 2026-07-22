## ADDED Requirements

### Requirement: fst Format Support

The system SHALL support reading R `fst` columnar files as iterable row dictionaries.

#### Scenario: Read fst rows

- **WHEN** a valid `.fst` file is opened via `open_iterable`
- **THEN** the system SHALL yield one dict record per row
- **AND** iteration SHALL NOT require loading the entire frame before the first yield

#### Scenario: Missing fst dependency

- **WHEN** fst support is requested without its optional dependency
- **THEN** the system SHALL raise an `ImportError` with installation instructions for the correct extra
