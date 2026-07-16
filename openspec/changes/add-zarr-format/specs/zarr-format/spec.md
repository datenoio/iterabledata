## ADDED Requirements

### Requirement: Zarr v2/v3 Detection and Dependency

The system SHALL support Zarr v2 and v3 stores through an optional `zarr` extra and SHALL detect registered local stores without classifying arbitrary directories as Zarr.

#### Scenario: Open local Zarr store

- **WHEN** a user opens a valid `.zarr` store through `open_iterable()`
- **THEN** the Zarr iterable SHALL be selected
- **AND** the store version SHALL be handled when supported

#### Scenario: Dependency missing

- **WHEN** a user opens Zarr without the required package installed
- **THEN** an `ImportError` SHALL name the `zarr` installation extra

#### Scenario: Ordinary directory

- **WHEN** a path is a directory without valid Zarr metadata
- **THEN** it SHALL NOT be silently accepted as a Zarr store

### Requirement: Zarr Array Discovery and Selection

The iterable SHALL expose arrays in a store as named tables and SHALL require deterministic array selection when more than one array could be read.

#### Scenario: List arrays

- **WHEN** `list_tables()` is called on a Zarr group
- **THEN** it SHALL return discoverable array paths in deterministic order

#### Scenario: Ambiguous store

- **WHEN** a store contains multiple arrays and no `array` option is supplied
- **THEN** the iterable SHALL raise a clear selection error
- **AND** the message SHALL identify available array paths

### Requirement: Bounded Zarr Row Iteration

Zarr arrays SHALL be read by chunks/slices with peak memory bounded by the selected chunk or batch, and SHALL use the documented structured, dense, or scalar row mapping.

#### Scenario: Structured array

- **WHEN** a structured array is selected
- **THEN** each element SHALL yield a dictionary keyed by field name
- **AND** iteration SHALL not materialize the complete array

#### Scenario: Dense multidimensional array

- **WHEN** a dense N-dimensional array is selected with default `axis=0`
- **THEN** each row SHALL contain its leading-axis index and selected slice values
- **AND** `slice` options SHALL be applied before value conversion

#### Scenario: Bulk exhaustion

- **WHEN** `read_bulk(n)` reaches the end of the selected array
- **THEN** it SHALL return the remaining partial batch and then `[]`

### Requirement: Chunk-Bounded Zarr Writing

The Zarr writer SHALL create or append compatible arrays in bounded chunks using explicit or first-batch-inferred schema/shape/dtype rules.

#### Scenario: Create and round-trip array

- **WHEN** compatible records are written to a new Zarr array
- **THEN** chunks SHALL be flushed without retaining the whole output
- **AND** reopening the array SHALL yield equivalent logical records

#### Scenario: Incompatible append

- **WHEN** later records have an incompatible shape, field set, or dtype
- **THEN** writing SHALL fail with a clear schema/shape error
- **AND** the writer SHALL NOT silently coerce destructive changes
