## ADDED Requirements

### Requirement: Delta Lake Write Support

The system SHALL support writing dictionary records to Delta Lake tables through the existing Delta iterable, using the `deltalake` client, with documented create/overwrite/append modes and bounded batch flushing where the backend allows.

#### Scenario: Append round trip

- **WHEN** supported records are written to a Delta table path with append or overwrite mode and then read back
- **THEN** the logical field values SHALL match for supported types

#### Scenario: Write mode selection

- **WHEN** a write mode is supplied in `iterableargs`
- **THEN** the Delta writer SHALL apply that mode when supported
- **AND** unsupported modes SHALL fail with a clear error

#### Scenario: Descriptor writable

- **WHEN** Delta write support is enabled
- **THEN** the format descriptor SHALL report the format as writable
- **AND** capability APIs SHALL no longer classify Delta as read-only
