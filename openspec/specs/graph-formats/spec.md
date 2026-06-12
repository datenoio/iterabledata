# graph-formats Specification

## Purpose
TBD - created by archiving change add-rdf-xlsb-fasta-graph-bio-formats. Update Purpose after archive.
## Requirements
### Requirement: GraphML Format Support
The system SHALL support reading and optionally writing GraphML files using NetworkX, exposing graph data as iterable records (nodes and/or edges).

#### Scenario: Read GraphML file with automatic detection
- **WHEN** user opens a file with extension `.graphml` via `open_iterable`
- **THEN** the system selects the GraphML iterable and yields node and/or edge records as dicts

#### Scenario: Read valid GraphML content
- **WHEN** reading a valid GraphML file
- **THEN** yielded records SHALL represent nodes and/or edges with attributes as defined by the implementation (e.g. node id, edge source/target, attributes)
- **AND** the system SHALL use NetworkX for parsing when the graph extra is installed

#### Scenario: Missing NetworkX dependency for GraphML
- **WHEN** NetworkX is not installed and user attempts to read a GraphML file
- **THEN** the system SHALL raise an ImportError with a message instructing to install the graph extra (e.g. `pip install iterabledata[graph]`)

### Requirement: GEXF Format Support
The system SHALL support reading and optionally writing GEXF (Graph Exchange XML Format) files using NetworkX, exposing graph data as iterable records.

#### Scenario: Read GEXF file with automatic detection
- **WHEN** user opens a file with extension `.gexf` via `open_iterable`
- **THEN** the system selects the GEXF iterable and yields node and/or edge records as dicts

#### Scenario: Read valid GEXF content
- **WHEN** reading a valid GEXF file
- **THEN** yielded records SHALL represent nodes and/or edges with attributes as defined by the implementation
- **AND** the system SHALL use NetworkX for parsing when the graph extra is installed

#### Scenario: Missing NetworkX dependency for GEXF
- **WHEN** NetworkX is not installed and user attempts to read a GEXF file
- **THEN** the system SHALL raise an ImportError with install instructions for the graph extra

### Requirement: DOT Format Support
The system SHALL support reading and optionally writing DOT (GraphViz) files using NetworkX, exposing graph data as iterable records.

#### Scenario: Read DOT file with automatic detection
- **WHEN** user opens a file with extension `.dot` or `.gv` via `open_iterable`
- **THEN** the system selects the DOT iterable and yields node and/or edge records as dicts

#### Scenario: Read valid DOT content
- **WHEN** reading a valid DOT file
- **THEN** yielded records SHALL represent nodes and/or edges with attributes as defined by the implementation
- **AND** the system SHALL use NetworkX for parsing when the graph extra is installed

#### Scenario: Missing NetworkX dependency for DOT
- **WHEN** NetworkX is not installed and user attempts to read a DOT file
- **THEN** the system SHALL raise an ImportError with install instructions for the graph extra

