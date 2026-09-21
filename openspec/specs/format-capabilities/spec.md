# format-capabilities Specification

## Purpose
TBD - created by archiving change add-format-capabilities. Update Purpose after archive.
## Requirements
### Requirement: Format Capability Query API
The system SHALL provide functions to query format capabilities programmatically, allowing users to discover what operations and features are supported by each data format.

#### Scenario: Query capabilities for a specific format
- **WHEN** user calls `get_format_capabilities("csv")`
- **THEN** system returns a dictionary with all capability flags for CSV format
- **AND** dictionary includes keys: `readable`, `writable`, `bulk_read`, `bulk_write`, `totals`, `streaming`, `flat_only`, `tables`, `compression`, `nested`
- **AND** values are boolean (True/False) or None for unknown capabilities

#### Scenario: List capabilities for all formats
- **WHEN** user calls `list_all_capabilities()`
- **THEN** system returns a dictionary mapping format IDs to their capability dictionaries
- **AND** all registered formats in the system are included
- **AND** each format entry contains the same capability keys

#### Scenario: Query a specific capability
- **WHEN** user calls `get_capability("json", "writable")`
- **THEN** system returns True if JSON format supports writing, False otherwise
- **AND** returns None if capability cannot be determined

#### Scenario: Handle unknown format
- **WHEN** user calls `get_format_capabilities("unknown_format")`
- **THEN** system raises ValueError with descriptive error message

#### Scenario: Handle missing optional dependencies
- **WHEN** user queries capabilities for a format requiring optional dependencies that are not installed
- **THEN** system returns capability dictionary with None values for capabilities that cannot be determined
- **AND** does not raise ImportError or crash

### Requirement: Capability Detection Logic

The system SHALL report built-in format capabilities from declarative format descriptors. Runtime method inspection MAY be used by conformance tests, but SHALL NOT optimistically infer a known capability that the descriptor declares as false or unknown.

#### Scenario: Detect read/write capabilities

- **WHEN** capability reporting loads a built-in descriptor
- **THEN** `readable` and `writable` SHALL match its explicit declarations
- **AND** aliases SHALL report the same values as the canonical format
- **AND** `bulk_read`/`bulk_write` SHALL indicate API availability

#### Scenario: Distinguish API and native bulk support

- **WHEN** a format inherits the base `read_bulk()` loop but has no optimized backend batch path
- **THEN** `bulk_read` SHALL indicate API availability
- **AND** `native_bulk_read` SHALL be `False`

#### Scenario: Detect totals support

- **WHEN** a descriptor declares totals support
- **THEN** `totals` SHALL match that declaration
- **AND** conformance tests SHALL compare it with `has_totals()` where the implementation is importable

#### Scenario: Detect table support

- **WHEN** a descriptor declares named-table support
- **THEN** `tables` SHALL match that declaration
- **AND** conformance tests SHALL compare it with `has_tables()` where the implementation is importable

#### Scenario: Detect flat-only support

- **WHEN** a descriptor declares a format flat-only
- **THEN** `flat_only` SHALL be `True`
- **AND** `nested` SHALL be `False`

#### Scenario: Detect streaming support

- **WHEN** a descriptor declares bounded incremental reading
- **THEN** `streaming` SHALL be `True`
- **AND** `read_memory` SHALL identify the declared bounded behavior

#### Scenario: Detect compression support

- **WHEN** capability reporting checks compression support
- **THEN** it SHALL use the descriptor's codec/source compatibility declaration
- **AND** it SHALL return `None` rather than assuming support when compatibility is unknown

### Requirement: Capability Caching
The system SHALL cache capability detection results to avoid repeated introspection of format classes.

#### Scenario: Cache capability results
- **WHEN** user queries capabilities for the same format multiple times
- **THEN** system returns cached results after first detection
- **AND** detection logic is only executed once per format class

#### Scenario: Cache invalidation not required
- **WHEN** format classes are not modified at runtime
- **THEN** cached capability results remain valid
- **AND** no cache invalidation mechanism is required

### Requirement: Capability Dictionary Structure
The system SHALL return capability information in a standardized dictionary format.

#### Scenario: Standard capability keys
- **WHEN** capability dictionary is returned
- **THEN** dictionary contains all standard capability keys:
  - `readable` (bool | None)
  - `writable` (bool | None)
  - `bulk_read` (bool | None)
  - `bulk_write` (bool | None)
  - `totals` (bool | None)
  - `streaming` (bool | None)
  - `flat_only` (bool | None)
  - `tables` (bool | None)
  - `compression` (bool | None)
  - `nested` (bool | None)

#### Scenario: Boolean or None values
- **WHEN** capability value is determined
- **THEN** value is True or False
- **WHEN** capability cannot be determined (e.g., missing dependencies)
- **THEN** value is None

### Requirement: Integration with Format Registry
The system SHALL integrate with the existing format detection and registry system.

#### Scenario: Access format registry
- **WHEN** capability functions need to enumerate formats
- **THEN** system uses format registry from `iterable/helpers/detect.py`
- **AND** format registry provides format IDs and class information

#### Scenario: Format ID consistency
- **WHEN** user queries capabilities using format ID
- **THEN** format ID matches IDs used in format registry
- **AND** format ID can be file extension or format name (e.g., "csv", "json", "parquet")

### Requirement: Extended Capability Structure

Capability dictionaries SHALL preserve existing keys and SHALL additionally expose native bulk support, read/write memory behavior, selection/pushdown support, source constraints, maturity, and catalog schema version.

#### Scenario: Query extended capabilities

- **WHEN** `get_format_capabilities()` returns a built-in format
- **THEN** the result SHALL include `native_bulk_read`, `native_bulk_write`, `read_memory`, `write_memory`, `selection`, `codec_support`, `source_constraints`, and `maturity`
- **AND** `source_constraints` SHALL carry path/stream/cloud restrictions (such as `filename` or `directory`)
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

