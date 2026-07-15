# ops-stats Specification

## Purpose
TBD - created by archiving change add-high-level-operations. Update Purpose after archive.
## Requirements
### Requirement: Comprehensive Statistics Computation
The system SHALL provide a function to compute comprehensive statistics for all fields in an
iterable dataset, with optional DuckDB engine support for performance, and SHALL optionally
report the null fraction, the most frequent values, and whether a field behaves as a
dictionary (lookup) field.

#### Scenario: Compute statistics with DuckDB
- **WHEN** `stats.compute()` is called on a CSV, JSONL, or JSON file with DuckDB engine available
- **THEN** statistics are computed efficiently using DuckDB pushdown
- **AND** the function returns a dictionary mapping field names to their statistics
- **AND** statistics include: count, min, max, mean, median, stddev (for numeric fields), unique count, null count

#### Scenario: Compute statistics with Python fallback
- **WHEN** `stats.compute()` is called without DuckDB engine or on unsupported format
- **THEN** statistics are computed using Python streaming iteration
- **AND** the function returns the same statistics dictionary structure
- **AND** computation handles large datasets efficiently

#### Scenario: Statistics with date detection
- **WHEN** `stats.compute()` is called with `detect_dates=True`
- **THEN** the function attempts to detect date fields
- **AND** date fields receive appropriate statistics (min, max, range)
- **AND** date parsing errors are handled gracefully

#### Scenario: Null fraction reporting
- **WHEN** `stats.compute()` is called
- **THEN** each field's statistics include a `null_fraction` between 0 and 1

#### Scenario: Top values and dictionary detection
- **WHEN** `stats.compute()` is called with `include_top_values=True`
- **THEN** each field's statistics include `top_values` with the most frequent values and their counts
- **AND** each field is flagged with `is_dictionary` based on the unique-to-total ratio compared to `dict_threshold`

### Requirement: Value Frequency Analysis
The system SHALL provide a function to compute frequency distributions for specified fields.

#### Scenario: Frequency analysis for single field
- **WHEN** `stats.frequency()` is called with an iterable and `fields=["status"]`
- **THEN** the function returns a dictionary mapping each unique value to its frequency count
- **AND** results are sorted by frequency (descending) by default
- **AND** the function handles large datasets efficiently

#### Scenario: Frequency analysis for multiple fields
- **WHEN** `stats.frequency()` is called with `fields=["status", "category"]`
- **THEN** the function returns frequency distributions for both fields
- **AND** results are organized by field name
- **AND** each field's frequencies are computed independently

#### Scenario: Frequency with limit
- **WHEN** `stats.frequency()` is called with `limit=10`
- **THEN** the function returns only the top 10 most frequent values per field
- **AND** results are sorted by frequency

### Requirement: Unique Value Detection
The system SHALL provide a function to identify unique rows or unique values for specified fields.

#### Scenario: Unique rows by fields
- **WHEN** `stats.uniq()` is called with an iterable and `fields=["email"]`
- **THEN** the function returns an iterator of unique rows based on the specified fields
- **AND** only the first occurrence of each unique combination is returned
- **AND** the function handles large datasets efficiently

#### Scenario: Unique values for field
- **WHEN** `stats.uniq()` is called with `fields=["status"]` and `values_only=True`
- **THEN** the function returns a set or list of unique values for the field
- **AND** duplicate values are excluded

#### Scenario: Unique with count
- **WHEN** `stats.uniq()` is called with `include_count=True`
- **THEN** the function returns unique rows/values along with their occurrence counts
- **AND** results include both the unique item and its frequency

### Requirement: Type Inference
The system SHALL provide type inference capabilities for dataset fields, detecting data types from sample data.

#### Scenario: Infer basic types
- **WHEN** type inference is performed on a dataset
- **THEN** the system detects common types: string, integer, float, boolean, date, datetime
- **AND** type detection handles mixed types gracefully (e.g., nullable fields)
- **AND** inference uses sampling for large datasets

#### Scenario: Infer date types
- **WHEN** type inference is performed with `detect_dates=True`
- **THEN** the system attempts to detect date and datetime fields
- **AND** common date formats are recognized
- **AND** date parsing errors don't prevent type inference

#### Scenario: Type inference with nulls
- **WHEN** type inference encounters null values
- **THEN** the system infers the type from non-null values
- **AND** nullability information is preserved
- **AND** mixed types are handled appropriately

