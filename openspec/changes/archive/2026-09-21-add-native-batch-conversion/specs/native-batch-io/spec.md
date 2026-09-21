## ADDED Requirements

### Requirement: Optional Native Batch Reader and Writer Protocols

The system SHALL provide optional protocols through which capable sources yield backend-native or registered interchange batches and capable destinations accept them. Formats without these protocols SHALL continue to support the existing row API.

#### Scenario: Compatible Arrow-native endpoints

- **WHEN** a Parquet source and Arrow-compatible destination both expose compatible native batch protocols
- **THEN** batches SHALL be transferred without conversion to `list[dict]`
- **AND** logical row order and values SHALL match row iteration

#### Scenario: Format has no native adapter

- **WHEN** either endpoint lacks a compatible native batch protocol
- **THEN** conversion SHALL use the existing row path
- **AND** public conversion behavior SHALL remain correct

#### Scenario: Optional dependency is absent

- **WHEN** PyArrow or another adapter dependency is not installed
- **THEN** core imports SHALL continue to work
- **AND** only the affected native adapter SHALL be unavailable

### Requirement: Selection and Pushdown Request

Native batch readers SHALL accept a standardized request containing supported column projection, predicate, table/variable, row-range, slice, and batch-size hints, and SHALL report which operations were honored.

#### Scenario: Narrow Parquet projection

- **WHEN** a user requests two columns from a wide Parquet source
- **THEN** the Parquet backend SHALL read only those columns
- **AND** unselected columns SHALL NOT be materialized as Python objects

#### Scenario: Scientific variable and slice

- **WHEN** a user requests a variable and multidimensional slice from a capable scientific format
- **THEN** the backend SHALL apply the selection before batch-to-row conversion
- **AND** returned indexes/values SHALL correspond to the requested slice

#### Scenario: Unsupported selection

- **WHEN** a backend cannot honor a requested selection field
- **THEN** normal mode SHALL use a documented fallback that preserves results
- **AND** strict mode SHALL raise a clear unsupported-selection error rather than silently ignoring it

### Requirement: Native and Row Semantic Equivalence

For an identical source, selection, and destination, native-batch and row conversion paths SHALL produce equivalent logical records and schemas within the documented type mappings.

#### Scenario: Null and nested values

- **WHEN** input contains nulls, lists, structs, dates, and timestamps supported by both endpoints
- **THEN** native and row paths SHALL preserve equivalent values and field order/schema rules

#### Scenario: Native path fails before commit

- **WHEN** batch schema negotiation or writing fails
- **THEN** conversion SHALL report the error and clean up consistently with the row path
- **AND** atomic output mode SHALL not replace the destination
