## ADDED Requirements

### Requirement: CDF File Reading
The system SHALL support reading NASA Common Data Format (CDF) files and yielding variable data as dictionary records, with optional handling of dimensions and attributes.

#### Scenario: Read CDF file with automatic detection
- **WHEN** using `open_iterable` on a `.cdf` file
- **THEN** it automatically selects `CDFIterable` for processing

#### Scenario: Read CDF variables as records
- **WHEN** reading a CDF file with one or more variables
- **THEN** it yields records containing variable data (e.g. variable name, dimensions, values) in a structured format suitable for streaming

#### Scenario: Handle CDF attributes
- **WHEN** reading a CDF file with global or variable attributes
- **THEN** it preserves attribute information in metadata or yielded records where appropriate

#### Scenario: Handle missing CDF dependency
- **WHEN** the CDF backend (e.g. `spacepy`) or required CDF C library is not available
- **THEN** it raises an `ImportError` (or equivalent) with a clear message instructing installation of `iterabledata[cdf]` and any external CDF library requirements
