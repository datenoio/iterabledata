# ops-filter Specification

## Purpose
TBD - created by archiving change add-high-level-operations. Update Purpose after archive.
## Requirements
### Requirement: Expression-Based Filtering
The system SHALL provide a function to filter rows using boolean expressions, with optional DuckDB engine support for performance.

#### Scenario: Filter with simple expression
- **WHEN** `filter.filter_expr()` is called with expression `"`status` == 'active'"`
- **THEN** the function returns an iterator containing only rows where status equals 'active'
- **AND** expression evaluation is safe (no arbitrary code execution)

#### Scenario: Filter with complex expression
- **WHEN** `filter.filter_expr()` is called with expression `"`status` == 'active' and `price` > 100"`
- **THEN** the function returns rows matching both conditions
- **AND** boolean operators (and, or, not) are supported
- **AND** comparison operators (==, !=, <, >, <=, >=) are supported

#### Scenario: Filter with DuckDB pushdown
- **WHEN** `filter.filter_expr()` is called on a CSV/JSONL file with DuckDB engine available
- **THEN** the filter is pushed down to DuckDB for efficient execution
- **AND** performance is significantly improved for large datasets
- **AND** results are identical to Python-based filtering

#### Scenario: Filter with Python fallback
- **WHEN** `filter.filter_expr()` is called without DuckDB engine or on unsupported format
- **THEN** the filter is evaluated using Python expression parsing
- **AND** filtering works correctly for all supported formats
- **AND** performance is acceptable for moderate-sized datasets

#### Scenario: Filter with field access
- **WHEN** `filter.filter_expr()` is called with expression referencing nested fields
- **THEN** nested field access is supported (e.g., `user.name`, `data.items[0]`)
- **AND** missing fields are handled gracefully (evaluate to None/null)

### Requirement: Regex Search Filtering
The system SHALL provide a function to filter rows using regular expression pattern matching.

#### Scenario: Search across all fields
- **WHEN** `filter.search()` is called with `pattern="error|warning"` and `fields=None`
- **THEN** the function searches for the pattern across all string fields in each row
- **AND** returns rows where the pattern matches in any field

#### Scenario: Search in specific fields
- **WHEN** `filter.search()` is called with `pattern="\d{3}-\d{3}-\d{4}"` and `fields=["phone", "mobile"]`
- **THEN** the function searches only in the specified fields
- **AND** returns rows where the pattern matches in any of the specified fields

#### Scenario: Case-insensitive search
- **WHEN** `filter.search()` is called with `pattern="ERROR"` and `ignore_case=True`
- **THEN** the search is case-insensitive
- **AND** matches "error", "Error", "ERROR", etc.

#### Scenario: Search with regex flags
- **WHEN** `filter.search()` is called with regex flags (multiline, dotall, etc.)
- **THEN** the flags are applied to pattern matching
- **AND** regex behavior matches Python's `re` module

### Requirement: Query Language Support
The system SHALL provide basic query language support for filtering and selecting data.

#### Scenario: Query with WHERE clause
- **WHEN** `filter.query_mistql()` is called with query `"SELECT * WHERE status = 'active'"`
- **THEN** the function returns rows matching the WHERE condition
- **AND** basic SQL-like syntax is supported

#### Scenario: Query with field selection
- **WHEN** `filter.query_mistql()` is called with query `"SELECT id, name WHERE price > 100"`
- **THEN** the function returns only specified fields for matching rows
- **AND** field selection works correctly

#### Scenario: Query with DuckDB optimization
- **WHEN** `filter.query_mistql()` is called with DuckDB engine available
- **THEN** the query is executed using DuckDB when possible
- **AND** performance is optimized for large datasets

### Requirement: Filter Expression Safety
The system SHALL ensure that filter expressions cannot execute arbitrary code or access unsafe operations.

#### Scenario: Safe expression evaluation
- **WHEN** `filter.filter_expr()` is called with any expression
- **THEN** expression evaluation is restricted to safe operations
- **AND** arbitrary code execution is prevented
- **AND** only field access, comparisons, and basic operators are allowed

#### Scenario: Malformed expression handling
- **WHEN** `filter.filter_expr()` is called with an invalid expression
- **THEN** the function raises a clear error message
- **AND** the error indicates the problem with the expression
- **AND** no partial filtering occurs

### Requirement: AI-Assisted Filter Execution
The system SHALL accept filter abstract syntax trees produced by `ai.translate_filter()` and apply
them through the existing filter operation layer.

#### Scenario: Apply AI-produced AST
- **WHEN** a filter AST from `ai.translate_filter()` is passed to the filter executor
- **THEN** rows are filtered according to the AST semantics
- **AND** behavior matches equivalent hand-written `ops.filter` expressions for supported nodes

#### Scenario: Reject unsupported AST nodes
- **WHEN** a filter AST contains a node type not in the whitelist
- **THEN** the executor raises a clear validation error before processing rows

