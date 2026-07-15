## MODIFIED Requirements

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
