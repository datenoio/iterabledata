## MODIFIED Requirements

### Requirement: Capability Detection Logic

The system SHALL report built-in format capabilities from declarative format descriptors. Runtime method inspection MAY be used by conformance tests, but SHALL NOT optimistically infer a known capability that the descriptor declares as false or unknown.

#### Scenario: Report read/write capabilities

- **WHEN** capability reporting loads a built-in descriptor
- **THEN** `readable` and `writable` SHALL match its explicit declarations
- **AND** aliases SHALL report the same values as the canonical format

#### Scenario: Distinguish API and native bulk support

- **WHEN** a format inherits the base `read_bulk()` loop but has no optimized backend batch path
- **THEN** `bulk_read` SHALL indicate API availability
- **AND** `native_bulk_read` SHALL be `False`

#### Scenario: Report totals and table support

- **WHEN** a descriptor declares totals or named-table support
- **THEN** `totals` and `tables` SHALL match those declarations
- **AND** conformance tests SHALL compare them with `has_totals()` and `has_tables()` where the implementation is importable

#### Scenario: Report flat and nested support

- **WHEN** a descriptor declares a format flat-only
- **THEN** `flat_only` SHALL be `True`
- **AND** `nested` SHALL be `False`

#### Scenario: Report streaming and memory behavior

- **WHEN** a descriptor declares bounded incremental reading
- **THEN** `streaming` SHALL be `True`
- **AND** `read_memory` SHALL identify the declared bounded behavior

#### Scenario: Report codec composition

- **WHEN** capability reporting checks compression support
- **THEN** it SHALL use the descriptor's codec/source compatibility declaration
- **AND** it SHALL return `None` rather than assuming support when compatibility is unknown

## ADDED Requirements

### Requirement: Extended Capability Structure

Capability dictionaries SHALL preserve existing keys and SHALL additionally expose native bulk support, read/write memory behavior, selection/pushdown support, source constraints, maturity, and catalog schema version.

#### Scenario: Query extended capabilities

- **WHEN** `get_format_capabilities()` returns a built-in format
- **THEN** the result SHALL include `native_bulk_read`, `native_bulk_write`, `read_memory`, `write_memory`, `selection`, `path_only`, `stream`, `cloud`, and `maturity`
- **AND** each field SHALL use its documented boolean, enum, structured, or unknown value

#### Scenario: Optional dependency is absent

- **WHEN** the implementation cannot be imported because an optional dependency is missing
- **THEN** static descriptor capabilities SHALL remain available
- **AND** only genuinely runtime-dependent fields SHALL be unknown

### Requirement: Capability Conformance

The project SHALL test declared capabilities against importable implementations and SHALL fail when method behavior or memory/bulk declarations contradict the descriptor.

#### Scenario: Writable declaration contradicts implementation

- **WHEN** a descriptor declares `writable=True` but the class uses the base unsupported writer
- **THEN** conformance testing SHALL fail with the format id and conflicting field

#### Scenario: Native bulk declaration

- **WHEN** a descriptor declares native bulk support
- **THEN** conformance testing SHALL verify a format-specific bulk implementation or backend batch path exists
- **AND** inherited base loops alone SHALL not satisfy the declaration
