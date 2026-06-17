# ops-inspect Specification

## Purpose
The `ops-inspect` capability provides dataset inspection operations: row counting, head/tail
sampling, header detection, file sniffing, structure analysis, and optional AI-powered
documentation via integration with `iterable.ai`.

## Requirements
### Requirement: Dataset Row Counting
The system SHALL provide a function to efficiently count rows in an iterable dataset, with optional DuckDB engine support for fast counting on supported formats.

#### Scenario: Count rows with DuckDB optimization
- **WHEN** `inspect.count()` is called on a CSV, JSONL, or JSON file with DuckDB engine available
- **THEN** the count is computed efficiently using DuckDB pushdown
- **AND** the function returns the total row count as an integer

#### Scenario: Count rows with Python fallback
- **WHEN** `inspect.count()` is called without DuckDB engine or on unsupported format
- **THEN** the count is computed using Python streaming iteration
- **AND** the function returns the total row count as an integer

### Requirement: Dataset Head Rows
The system SHALL provide a function to retrieve the first N rows from an iterable dataset.

#### Scenario: Get first rows
- **WHEN** `inspect.head()` is called with an iterable and `n=10`
- **THEN** the function returns an iterator yielding the first 10 rows
- **AND** the original iterable is not consumed beyond the first N rows

#### Scenario: Head with empty dataset
- **WHEN** `inspect.head()` is called on an empty iterable
- **THEN** the function returns an empty iterator
- **AND** no errors are raised

### Requirement: Dataset Tail Rows
The system SHALL provide a function to retrieve the last N rows from an iterable dataset.

#### Scenario: Get last rows
- **WHEN** `inspect.tail()` is called with an iterable and `n=10`
- **THEN** the function returns a list containing the last 10 rows
- **AND** the function handles datasets smaller than N rows gracefully

#### Scenario: Tail with small dataset
- **WHEN** `inspect.tail()` is called with `n=100` on a dataset with 5 rows
- **THEN** the function returns a list containing all 5 rows
- **AND** no errors are raised

### Requirement: Column Header Detection
The system SHALL provide a function to detect column names from an iterable dataset.

#### Scenario: Get headers from dataset
- **WHEN** `inspect.headers()` is called with an iterable
- **THEN** the function returns a list of column names
- **AND** column names are extracted from the first row's keys
- **AND** the function handles empty datasets gracefully

#### Scenario: Headers with limit
- **WHEN** `inspect.headers()` is called with `limit=50000` on a large dataset
- **THEN** the function processes up to the limit to detect headers
- **AND** returns column names based on the sampled rows

### Requirement: File Format Sniffing
The system SHALL provide a function to detect file format, encoding, compression, and other metadata from a file path.

#### Scenario: Sniff CSV file
- **WHEN** `inspect.sniff()` is called with a CSV file path
- **THEN** the function returns a dictionary containing:
  - `format`: detected format (e.g., "csv")
  - `encoding`: detected encoding (e.g., "utf-8")
  - `delimiter`: detected delimiter (e.g., ",")
  - `compression`: detected compression (e.g., "gzip" or None)
  - `has_header`: boolean indicating if header row exists

#### Scenario: Sniff compressed JSONL file
- **WHEN** `inspect.sniff()` is called with a `.jsonl.gz` file path
- **THEN** the function detects format as "jsonl"
- **AND** detects compression as "gzip"
- **AND** detects encoding appropriately

### Requirement: Dataset Structure Analysis
The system SHALL provide a function to analyze dataset structure, field types, and generate metadata about the dataset.

#### Scenario: Analyze dataset structure
- **WHEN** `inspect.analyze()` is called with an iterable
- **THEN** the function returns a dictionary containing:
  - `row_count`: total number of rows (if calculable)
  - `fields`: dictionary mapping field names to metadata (type, nullability, sample values)
  - `structure`: overall structure information
- **AND** the analysis is performed efficiently using sampling when needed

#### Scenario: Analyze with autodoc disabled
- **WHEN** `inspect.analyze()` is called with `autodoc=False`
- **THEN** the function performs structure analysis without AI-powered documentation
- **AND** returns basic field metadata and type information

#### Scenario: Analyze with autodoc enabled
- **WHEN** `inspect.analyze()` is called with `autodoc=True` and AI dependencies available
- **THEN** the function performs structure analysis
- **AND** calls `iterable.ai.doc.generate()` using the dataset path or analyzed rows
- **AND** includes `documentation` and `documentation_meta` in the result
- **AND** merges AI field descriptions into field metadata when enabled

#### Scenario: Analyze with autodoc and missing AI dependencies
- **WHEN** `inspect.analyze()` is called with `autodoc=True` and AI optional dependencies are not installed
- **THEN** the function raises `ImportError` with installation instructions
- **AND** does not return a partial result silently

