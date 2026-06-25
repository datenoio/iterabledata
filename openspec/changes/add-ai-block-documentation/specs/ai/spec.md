## ADDED Requirements

### Requirement: Block-Based Documentation Generation
The system SHALL provide `ai.doc.generate_blocks()` that generates dataset documentation as
independent blocks and returns a structured result containing per-block markdown and data
plus an assembled full document.

#### Scenario: Generate selected blocks
- **WHEN** `ai.doc.generate_blocks()` is called with `blocks=["general", "schema"]`
- **THEN** the result contains a `blocks` mapping with entries for `general` and `schema`
- **AND** each block entry contains a `markdown` string and a `data` dictionary
- **AND** the result contains a `source` descriptor and a `full_document_markdown` string

#### Scenario: Default block set
- **WHEN** `ai.doc.generate_blocks()` is called without an explicit `blocks` list
- **THEN** the default v1 blocks are generated (general, schema, quality, examples, statistics)
- **AND** unknown block names raise a clear error

#### Scenario: Deferred blocks are registered but not implemented
- **WHEN** `ai.doc.generate_blocks()` is called with a deferred block such as `geo_coverage` or `lineage`
- **THEN** the block entry indicates the block is not implemented in this version
- **AND** generation of other requested blocks still succeeds

### Requirement: Backward-Compatible Documentation Function
The system SHALL keep `ai.doc.generate()` backward compatible by delegating to the
block-based engine while preserving its existing signature and return types.

#### Scenario: Existing generate call unchanged
- **WHEN** `ai.doc.generate("data.csv", format="markdown")` is called
- **THEN** a markdown string is returned as before
- **AND** `format="json"` returns a dictionary as before

### Requirement: Structured Output via JSON Schema
The system SHALL generate each documentation block using structured output constrained by a
JSON Schema, validated against Pydantic models, with graceful fallback when a provider does
not support schema-constrained responses.

#### Scenario: Structured output with schema support
- **WHEN** a block is generated with a provider that supports JSON-Schema responses
- **THEN** the provider is asked for a schema-constrained JSON response
- **AND** the response is validated against the block's Pydantic model

#### Scenario: Fallback when schema mode unsupported
- **WHEN** a provider does not support JSON-Schema responses
- **THEN** the system falls back to JSON-object mode or text extraction
- **AND** the parsed result is still validated against the block's model
- **AND** documentation generation still succeeds

### Requirement: User Context Parameter
The system SHALL accept a user-supplied `context` (such as title, description, tags,
territory, source URL, and dataset-card metadata) and incorporate it into block prompts.

#### Scenario: Context influences generation
- **WHEN** `generate_blocks()` is called with `context={"title": "Census", "territory": "Russia"}`
- **THEN** the provided context is included in the prompts sent to the LLM
- **AND** the `general` block data reflects the supplied context fields

### Requirement: In-Process Progress Hooks
The system SHALL provide an in-process progress callback mechanism with defined processing
stages, invoked as block generation proceeds, without requiring any external task queue.

#### Scenario: Progress callback invoked per stage
- **WHEN** `generate_blocks()` is called with a `progress` callback
- **THEN** the callback is invoked with stage updates (for example parsing, sampling, generating, assembling, completed)
- **AND** each progress event includes a stage identifier and a percentage

#### Scenario: Failure stage reported
- **WHEN** generation fails during a stage
- **THEN** the callback receives a failed stage event before the error propagates

### Requirement: Per-Stage Structured Logging
The system SHALL emit structured log events for each processing stage, including a job
identifier, stage name, duration, and LLM token usage when available.

#### Scenario: Stage logs include context
- **WHEN** structured logging is enabled during `generate_blocks()`
- **THEN** each stage emits a structured event with `job_id`, `stage`, and `duration_ms`
- **AND** generation stages include token usage when the provider reports it

### Requirement: Size-Based Sampling Strategy
The system SHALL select an LLM sampling strategy based on input size, configurable via
`MAX_ROWS_SAMPLING`.

#### Scenario: Small input full sampling
- **WHEN** the input is small (under the small-file threshold)
- **THEN** the schema and the first N rows are sampled

#### Scenario: Medium input mixed sampling
- **WHEN** the input is medium-sized
- **THEN** the schema, the first N rows, and N random rows are sampled

#### Scenario: Large input schema-only sampling
- **WHEN** the input exceeds the large-file threshold
- **THEN** only schema and statistics are used and no data rows are sent to the LLM

### Requirement: File Metadata Extraction
The system SHALL extract file-level metadata for documentation, including file name, size,
content hash, detected format, encoding (for text formats), record count, and table count.

#### Scenario: Extract metadata for a file
- **WHEN** documentation is generated for a file path
- **THEN** the `general` block data and `source` descriptor include file size and a content hash
- **AND** table count reflects the number of tables/sheets for multi-table formats

### Requirement: Multi-Table Documentation
The system SHALL document multi-table formats (such as XLSX and XLS) by listing available
tables and generating a schema block per selected table, with an optional `tables` selection.

#### Scenario: Document selected tables
- **WHEN** `generate_blocks()` is called on a multi-sheet workbook with `tables=["Sheet1"]`
- **THEN** only the selected table is documented
- **AND** the `general` block lists all available tables

### Requirement: Environment-Driven Provider Configuration
The system SHALL resolve LLM provider configuration from `LLM_PROVIDER`, `LLM_BASE_URL`,
`LLM_API_KEY`, and `LLM_DEFAULT_MODEL` environment variables, and SHALL support a generic
OpenAI-compatible provider configured via `LLM_BASE_URL`.

#### Scenario: Resolve provider from environment
- **WHEN** `LLM_PROVIDER` and related variables are set and no explicit provider is passed
- **THEN** the configured provider and defaults are used

#### Scenario: Generic OpenAI-compatible endpoint
- **WHEN** a generic OpenAI-compatible provider is selected with `LLM_BASE_URL`
- **THEN** requests are sent to the configured base URL using the OpenAI-compatible client

### Requirement: Wide Schema Token Management
The system SHALL batch schema-block generation for datasets with many columns to stay within
LLM context limits, aggregating field results across batches.

#### Scenario: Batch wide schemas
- **WHEN** a dataset has more than 100 columns
- **THEN** the schema block is generated in column batches
- **AND** the resulting `fields` are merged into a single schema block
