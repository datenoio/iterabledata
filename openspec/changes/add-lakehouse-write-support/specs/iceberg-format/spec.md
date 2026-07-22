## ADDED Requirements

### Requirement: Iceberg Write Support

The system SHALL support writing dictionary records to Apache Iceberg tables through the existing Iceberg iterable and PyIceberg catalog/table APIs, with documented append (and create/overwrite when safe) modes.

#### Scenario: Append round trip

- **WHEN** supported records are appended to an Iceberg table identified by catalog and table coordinates and then read back
- **THEN** the new rows SHALL be visible according to commit semantics

#### Scenario: Catalog coordinates required

- **WHEN** Iceberg write mode is requested without required catalog/table options
- **THEN** the system SHALL raise a clear configuration error

#### Scenario: Descriptor writable

- **WHEN** Iceberg write support is enabled
- **THEN** the format descriptor SHALL report the format as writable
- **AND** capability APIs SHALL no longer classify Iceberg as read-only
