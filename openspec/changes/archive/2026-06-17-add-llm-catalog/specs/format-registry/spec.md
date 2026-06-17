## MODIFIED Requirements

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
