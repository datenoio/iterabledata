## ADDED Requirements

### Requirement: GeoJSON Text Sequence Support

The system SHALL provide a `geojsonseq` format that reads and writes GeoJSON Text Sequences (RFC 8142), where each line is a single GeoJSON Feature object, optionally prefixed by the record-separator control character `\x1e`. Reading and writing SHALL stream one feature at a time.

#### Scenario: Read features line by line

- **WHEN** a `.geojsonl` file with one Feature per line is opened via `open_iterable()`
- **THEN** iteration SHALL yield one record per feature
- **AND** peak memory SHALL be bounded by a single feature, not the file size

#### Scenario: Tolerate RFC 8142 record separator

- **WHEN** a GeoJSON sequence uses the `\x1e` record separator before each JSON text
- **THEN** the reader SHALL strip the separator and parse each feature correctly

#### Scenario: Write one feature per line

- **WHEN** records are written to a `geojsonseq` target
- **THEN** each record SHALL be serialized as a single-line GeoJSON Feature object
- **AND** the output SHALL be re-readable by the same format
