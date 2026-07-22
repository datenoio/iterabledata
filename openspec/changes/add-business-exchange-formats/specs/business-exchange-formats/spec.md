## ADDED Requirements

### Requirement: EDI Format Support

The system SHALL support reading EDI documents for a documented X12/EDIFACT subset and SHALL yield iterable segment or transaction records as documented.

#### Scenario: Read EDI segments

- **WHEN** a valid EDI file is opened via `open_iterable`
- **THEN** the system SHALL yield records containing segment identifiers and elements according to the documented mapping

#### Scenario: Unsupported EDI dialect

- **WHEN** an EDI dialect outside the supported subset is opened
- **THEN** the system SHALL raise a clear error identifying the limitation

### Requirement: Microsoft Access MDB Support

The system SHALL support reading Microsoft Access `.mdb` databases (and `.accdb` if declared in scope), list tables, and stream selected table rows as dictionaries.

#### Scenario: List and select Access tables

- **WHEN** an Access database contains multiple tables
- **THEN** `list_tables()` SHALL return table names
- **AND** opening without a table selection SHALL raise a clear error when more than one table exists

#### Scenario: Read Access table rows

- **WHEN** a selected Access table is opened
- **THEN** the system SHALL yield one dict record per row
- **AND** SHALL NOT require loading the entire table before the first yield

#### Scenario: Missing Access dependency

- **WHEN** Access support is requested without its optional dependency
- **THEN** the system SHALL raise an `ImportError` with installation instructions for the correct extra

### Requirement: Lotus 1-2-3 Format Support

The system SHALL support reading Lotus 1-2-3 `.123` spreadsheets as iterable row dictionaries.

#### Scenario: Read Lotus spreadsheet rows

- **WHEN** a valid `.123` file is opened via `open_iterable`
- **THEN** the system SHALL yield row records
- **AND** when a header row is configured or detected, keys SHALL use header names
