# format-registry Specification

## Purpose
The format registry provides a single declarative source of truth for built-in format metadata,
driving detection lists, capability reporting, and LLM-oriented catalog exports.

## Requirements

### Requirement: Declarative Format Descriptors
The system SHALL define each built-in format with a single declarative descriptor that records
its canonical id, aliases, implementing module and class, whether its content is text or binary,
whether it is flat/tabular, whether it supports writing, its optional-dependency extra (if any),
any leading-byte signatures used for content-based detection, and optional LLM-oriented metadata
(human description, example `iterableargs`, known limitations, documentation URL). The set of
descriptors SHALL be the single source of truth for built-in format metadata.

#### Scenario: Each format has exactly one descriptor
- **WHEN** the format descriptor table is loaded
- **THEN** every built-in format id maps to exactly one descriptor
- **AND** every alias resolves to the same implementing module and class as its descriptor's canonical id

#### Scenario: Adding a format requires one entry
- **WHEN** a new built-in format is added
- **THEN** adding a single descriptor entry is sufficient for it to appear in the format registry, the read-only/text/flat classifications, and content detection

#### Scenario: LLM metadata available on descriptor
- **WHEN** `get_descriptor()` returns a descriptor for a format with curated LLM fields
- **THEN** the descriptor includes `description`, `example_args`, `limitations`, and `doc_url` when set
- **AND** unset LLM fields default to empty or None without affecting legacy derivation

### Requirement: Backward-Compatible Derived Structures
The system SHALL derive the existing module-level structures `DATATYPE_REGISTRY`,
`READ_ONLY_FORMATS`, `TEXT_DATA_TYPES`, and `FLAT_TYPES` from the descriptor table, preserving
their names, types, and contents so existing importers continue to work unchanged.

#### Scenario: Derived registry matches prior contents
- **WHEN** the derived `DATATYPE_REGISTRY`, `READ_ONLY_FORMATS`, `TEXT_DATA_TYPES`, and `FLAT_TYPES` are compared against the previously hand-maintained literals
- **THEN** the derived values are equal in content (and equal in order for the ordered lists)

#### Scenario: Write capability is single-sourced
- **WHEN** a descriptor declares a format as not writable
- **THEN** that format's id and all its aliases appear in the derived `READ_ONLY_FORMATS`
- **AND** the format capability layer reports the format as non-writable

### Requirement: Data-Driven Content Detection
The system SHALL match leading-byte signatures during content-based detection using the `magic`
data on descriptors, while preserving the existing detection precedence, confidence scores, and
reported detection method.

#### Scenario: Magic-byte match is unchanged
- **WHEN** a file whose leading bytes match a descriptor signature is detected by content
- **THEN** the detected format id, confidence score, and detection method equal those produced before this change

### Requirement: Descriptor Lookup API
The system SHALL expose a lookup API to retrieve a descriptor by id or alias and to iterate all
descriptors, for use by capability reporting, documentation generation, and conformance testing.

#### Scenario: Lookup by id or alias
- **WHEN** a descriptor is requested by a canonical id or by one of its aliases
- **THEN** the same descriptor is returned

#### Scenario: Unknown id lookup
- **WHEN** a descriptor is requested for an id that is not registered
- **THEN** the lookup reports the id as not found rather than returning an unrelated descriptor
