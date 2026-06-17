## ADDED Requirements

### Requirement: Format Catalog API
The system SHALL provide an `iterable.catalog` module for machine-readable format discovery
that merges declarative registry metadata with runtime capability flags.

#### Scenario: List all formats
- **WHEN** `catalog.list_formats()` is called
- **THEN** the function returns a sorted list of canonical format ids
- **AND** alias mappings are available via `describe_format()` or export

#### Scenario: Describe a format by id or alias
- **WHEN** `catalog.describe_format("tsv")` is called
- **THEN** the function returns metadata for the canonical format (csv) including aliases, text/flat/writable flags, optional extra, example args, limitations, and capabilities when requested
- **AND** unknown ids raise a clear error

#### Scenario: Export full catalog as JSON
- **WHEN** `catalog.export_catalog(format="json", include_capabilities=True)` is called
- **THEN** the function returns a JSON-serializable structure keyed by format id
- **AND** each entry includes descriptor fields and capability flags when available

### Requirement: LLM Context Sampling
The system SHALL provide utilities to build bounded, safe samples from iterables for LLM prompts.

#### Scenario: Sample with row limit
- **WHEN** `sample_for_llm(iterable, max_rows=10)` is called
- **THEN** the function returns at most 10 row dictionaries suitable for serialization to JSON in a prompt
- **AND** does not load unbounded data into memory

#### Scenario: Stratified sampling on large inputs
- **WHEN** `sample_for_llm()` is called with `strategy="stratified"` on a large iterable
- **THEN** the function returns a representative spread of rows across the dataset
- **AND** respects `max_rows` and optional `max_tokens` budget parameters

### Requirement: LLM Context Redaction
The system SHALL provide utilities to redact sensitive values from samples before external LLM calls.

#### Scenario: Redact common PII patterns
- **WHEN** `redact_for_llm(rows)` is called on rows containing email or phone-like fields
- **THEN** sensitive values are masked in the returned rows
- **AND** field names are preserved for schema context

#### Scenario: Redact with Metacrafter PII fields
- **WHEN** `redact_for_llm()` is called with a Metacrafter PII field list
- **THEN** identified PII columns are masked
- **AND** the function degrades gracefully when Metacrafter data is unavailable

### Requirement: Catalog CI Artifact
The project SHALL maintain a committed `dev/formats.json` export generated from the catalog API,
with CI verification when the format registry changes.

#### Scenario: formats.json matches catalog export
- **WHEN** CI runs the catalog drift check
- **THEN** `dev/formats.json` equals the output of `export_formats_json.py`
- **AND** the job fails if they differ without an intentional update
