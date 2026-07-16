## ADDED Requirements

### Requirement: Native Batch Conversion Path

`convert()` SHALL select a compatible native-batch path when both endpoints support it and requested operations do not require per-row materialization. It SHALL otherwise use the existing row path without changing results.

#### Scenario: Columnar-to-columnar conversion

- **WHEN** a compatible Parquet, Arrow, ORC, or lakehouse source is converted to a compatible batch destination without row-only transforms
- **THEN** `convert()` SHALL transfer native batches
- **AND** SHALL avoid an intermediate `list[dict]` representation

#### Scenario: Flattening is requested

- **WHEN** `is_flatten=True` requires per-row transformation
- **THEN** `convert()` SHALL use the row path unless a batch transform explicitly implements identical semantics
- **AND** output SHALL match existing flattening behavior

#### Scenario: Progress and metrics

- **WHEN** conversion uses native batches
- **THEN** `rows_read`, `rows_written`, elapsed time, errors, and progress callbacks SHALL reflect logical rows consistently with the row path

### Requirement: Conversion Selection Pushdown

`convert()` SHALL pass declared projection, predicate, table/variable, range, and slice requests to capable source adapters before materialization.

#### Scenario: Supported projection and filter

- **WHEN** the source declares both projection and filter pushdown
- **THEN** `convert()` SHALL request them from the backend
- **AND** only matching selected data SHALL reach the conversion layer

#### Scenario: Selection fallback

- **WHEN** a requested operation is not supported natively
- **THEN** `convert()` SHALL either apply the documented row fallback or raise in strict mode
- **AND** it SHALL report the selected path in debug diagnostics
