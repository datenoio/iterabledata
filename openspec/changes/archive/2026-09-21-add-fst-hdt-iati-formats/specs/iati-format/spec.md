## ADDED Requirements

### Requirement: IATI Format Support

The system SHALL support reading IATI XML documents as iterable activity records (or a documented finer grain such as transactions).

#### Scenario: Read IATI activities

- **WHEN** a valid IATI XML file is opened via `open_iterable` with the IATI format
- **THEN** the system SHALL yield one record per `iati-activity` (or documented unit)
- **AND** parsing SHALL stream sufficiently to avoid requiring the entire document tree in memory when practical

#### Scenario: Missing XML dependency for IATI

- **WHEN** IATI parsing requires the XML extra and it is not installed
- **THEN** the system SHALL raise an `ImportError` with installation instructions for the xml extra
