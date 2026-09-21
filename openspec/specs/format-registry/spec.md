# format-registry Specification

## Purpose
The format registry provides a single declarative source of truth for built-in format metadata,
driving detection lists, capability reporting, and LLM-oriented catalog exports.
## Requirements
### Requirement: Declarative Format Descriptors

The system SHALL define each built-in format with a single declarative descriptor that records its canonical id, aliases, implementing module and class, text/binary and flat/nested behavior, read/write and API/native bulk support, totals/tables, optional-dependency extra, leading-byte signatures, maturity, read/write memory behavior, codec composition, selection/pushdown support, path/stream/cloud constraints, and optional LLM-oriented metadata. The descriptors SHALL be the single source of truth for built-in format metadata.

#### Scenario: Each format has exactly one descriptor

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

### Requirement: Resolvable Dependency Extras

Every format descriptor whose implementation requires an optional third-party package SHALL map to an optional-dependency extra declared in `pyproject.toml` that installs the required package(s), and the install hint reported on `ImportError` SHALL name that extra. The `all` extra SHALL include every pip-installable optional dependency referenced by any format extra.

#### Scenario: Install hint resolves to a real extra

- **WHEN** opening a format whose optional dependency is not installed raises `ImportError`
- **THEN** the error message SHALL name an extra that exists in `pyproject.toml`
- **AND** installing that extra SHALL provide the package(s) the format module imports

#### Scenario: Lakehouse formats are installable

- **WHEN** a user installs the extra named in the install hint for `delta`, `iceberg`, or `lance`
- **THEN** the corresponding format module SHALL import successfully
- **AND** the hint SHALL NOT point at an extra (such as `parquet`) that does not include the format's required package

#### Scenario: The all extra is complete

- **WHEN** a user installs `iterabledata[all]`
- **THEN** every pip-installable package referenced by any format or codec extra SHALL be installed
- **AND** no registered format SHALL raise `ImportError` for a package that is available on PyPI

### Requirement: Descriptor Metadata Consistency

LLM-oriented descriptor metadata (descriptions, limitations) and format documentation pages SHALL be consistent with the descriptor's capability flags and the implementation. A descriptor with `writable=True` SHALL NOT carry metadata or documentation stating the format is read-only.

#### Scenario: Writable format metadata does not claim read-only

- **WHEN** a descriptor declares `writable=True`
- **THEN** its `limitations` metadata SHALL NOT contain a read-only claim
- **AND** the corresponding page under `docs/docs/formats/` SHALL NOT state that writing is unsupported

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

