## ADDED Requirements

### Requirement: TriG Format Support
The system SHALL support reading and optionally writing TriG (RDF Triple Graph) files using rdflib, yielding quad records (subject, predicate, object, graph).

#### Scenario: Read TriG file with automatic detection
- **WHEN** user opens a file with extension `.trig` via `open_iterable`
- **THEN** the system selects the TriG iterable and yields quad records as dicts

#### Scenario: Read valid TriG content
- **WHEN** reading a valid TriG file
- **THEN** each yielded record SHALL contain subject, predicate, object, and graph keys
- **AND** records are streamed without loading the entire graph into memory where practical

#### Scenario: Missing rdflib dependency
- **WHEN** rdflib is not installed and user attempts to read a TriG file
- **THEN** the system SHALL raise an ImportError with a message instructing to install the rdf extra (e.g. `pip install iterabledata[rdf]`)

### Requirement: N3 Format Support
The system SHALL support reading and optionally writing N3 (Notation3) files using rdflib, yielding triple records (subject, predicate, object).

#### Scenario: Read N3 file with automatic detection
- **WHEN** user opens a file with extension `.n3` via `open_iterable`
- **THEN** the system selects the N3 iterable and yields triple records as dicts

#### Scenario: Read valid N3 content
- **WHEN** reading a valid N3 file
- **THEN** each yielded record SHALL contain subject, predicate, and object keys
- **AND** records are streamed where practical

#### Scenario: Missing rdflib for N3
- **WHEN** rdflib is not installed and user attempts to read an N3 file
- **THEN** the system SHALL raise an ImportError with install instructions for the rdf extra

### Requirement: TriX Format Support
The system SHALL support reading and optionally writing TriX (XML Triple format) files using rdflib, yielding triple or quad records.

#### Scenario: Read TriX file with automatic detection
- **WHEN** user opens a file with extension `.trix` via `open_iterable`
- **THEN** the system selects the TriX iterable and yields triple/quad records as dicts

#### Scenario: Read valid TriX content
- **WHEN** reading a valid TriX file
- **THEN** each yielded record SHALL contain at least subject, predicate, and object keys
- **AND** records are streamed where practical

#### Scenario: Missing rdflib for TriX
- **WHEN** rdflib is not installed and user attempts to read a TriX file
- **THEN** the system SHALL raise an ImportError with install instructions for the rdf extra
