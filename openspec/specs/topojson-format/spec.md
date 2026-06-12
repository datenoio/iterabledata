# topojson-format Specification

## Purpose
TBD - created by archiving change add-additional-formats. Update Purpose after archive.
## Requirements
### Requirement: TopoJSON File Reading
The system SHALL support reading TopoJSON files and yielding geographic features as dictionary records.

#### Scenario: Read TopoJSON file with automatic detection
- **WHEN** using `open_iterable` on a `.topojson` file
- **THEN** it automatically selects `TopoJSONIterable` for processing

#### Scenario: Read TopoJSON features
- **WHEN** reading a TopoJSON file with geographic features
- **THEN** it yields records containing feature geometries and properties

#### Scenario: Handle TopoJSON topology
- **WHEN** reading a TopoJSON file with shared topology (arcs)
- **THEN** it properly decodes topology and reconstructs feature geometries

#### Scenario: Handle TopoJSON geometry types
- **WHEN** reading TopoJSON features with different geometry types
- **THEN** it properly represents geometries in the yielded records

#### Scenario: Handle missing dependency
- **WHEN** `topojson` is not installed
- **THEN** it raises an `ImportError` with a helpful message instructing to install `iterabledata[topojson]` or `iterabledata[geospatial]`

### Requirement: Valid TopoJSON structure on write
TopoJSONIterable.write_bulk MUST produce a valid TopoJSON document: a single JSON object with `"type": "Topology"`, and MUST NOT output a sequence of concatenated JSON objects.

#### Scenario: Writing TopoJSON
- **WHEN** a user writes geometry records with `write_bulk`
- **THEN** the output SHALL be valid TopoJSON starting with `{"type": "Topology"`
- **AND** geometries SHALL be placed under the topology `objects` structure

