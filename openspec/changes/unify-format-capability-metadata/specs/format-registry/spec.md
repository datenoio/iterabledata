## MODIFIED Requirements

### Requirement: Declarative Format Descriptors

The system SHALL define each built-in format with a single declarative descriptor that records its canonical id, aliases, implementing module and class, text/binary and flat/nested behavior, read/write and API/native bulk support, totals/tables, optional-dependency extra, leading-byte signatures, maturity, read/write memory behavior, codec composition, selection/pushdown support, path/stream/cloud constraints, and optional LLM-oriented metadata. The descriptors SHALL be the single source of truth for built-in format metadata.

#### Scenario: Each format has exactly one complete descriptor

- **WHEN** the format descriptor table is loaded
- **THEN** every built-in canonical format id SHALL map to exactly one descriptor
- **AND** every required field SHALL contain an explicit value or documented unknown
- **AND** every alias SHALL resolve to the same descriptor

#### Scenario: Adding a format requires one entry

- **WHEN** a new built-in format is added
- **THEN** adding one descriptor plus its implementation SHALL be sufficient for it to appear in detection, derived classifications, capability reporting, install hints, catalog export, and docs matrices

#### Scenario: LLM metadata available on descriptor

- **WHEN** `get_descriptor()` returns a descriptor with curated LLM fields
- **THEN** it SHALL include `description`, `example_args`, `limitations`, and `doc_url` when set
- **AND** unset optional LLM fields SHALL default to empty or `None` without changing other metadata

## ADDED Requirements

### Requirement: Generated Metadata Consumers

Legacy registries, read-only/text/flat collections, dependency hints, magic detection, capability dictionaries, catalog output, and documentation matrices SHALL be derived from descriptors and SHALL NOT maintain competing hand-written format facts.

#### Scenario: Generated structures match descriptors

- **WHEN** the generation/conformance check runs
- **THEN** every exported format fact SHALL trace to its canonical descriptor
- **AND** no alias, install extra, magic signature, or capability SHALL differ between consumers

#### Scenario: Descriptor changes

- **WHEN** a descriptor field changes
- **THEN** generated outputs SHALL change deterministically
- **AND** check mode SHALL fail until committed generated artifacts are updated

### Requirement: Versioned Catalog Schema

Machine-readable format catalog exports SHALL include a schema version and a documented compatibility policy.

#### Scenario: Catalog is exported

- **WHEN** the catalog JSON is generated
- **THEN** it SHALL include a schema version
- **AND** every format entry SHALL conform to the documented versioned shape

#### Scenario: Incompatible catalog change

- **WHEN** a field is removed or its meaning/type changes incompatibly
- **THEN** the catalog major schema version SHALL increase
