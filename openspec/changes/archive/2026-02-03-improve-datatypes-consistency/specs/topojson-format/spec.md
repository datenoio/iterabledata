# topojson-format (delta)

## ADDED Requirements

### Requirement: Valid TopoJSON structure on write
TopoJSONIterable.write_bulk MUST produce a valid TopoJSON document: a single JSON object with `"type": "Topology"`, and MUST NOT output a sequence of concatenated JSON objects.

#### Scenario: Writing TopoJSON
- **WHEN** a user writes geometry records with `write_bulk`
- **THEN** the output SHALL be valid TopoJSON starting with `{"type": "Topology"`
- **AND** geometries SHALL be placed under the topology `objects` structure
