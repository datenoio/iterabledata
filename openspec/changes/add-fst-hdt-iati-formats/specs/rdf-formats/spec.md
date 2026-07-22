## ADDED Requirements

### Requirement: RDF HDT Format Support

The system SHALL support reading RDF HDT files as iterable triple records compatible with the project's RDF record conventions.

#### Scenario: Read HDT triples

- **WHEN** a valid `.hdt` file is opened via `open_iterable`
- **THEN** the system SHALL yield triple records with subject, predicate, and object fields
- **AND** iteration SHALL stream without requiring a full in-memory triple list before the first yield

#### Scenario: Missing HDT dependency

- **WHEN** HDT support is requested without its optional dependency
- **THEN** the system SHALL raise an `ImportError` with installation instructions for the correct extra
