# ai Specification

## Purpose
TBD - created by archiving change add-high-level-operations. Update Purpose after archive.
## Requirements
### Requirement: AI-Powered Documentation Generation
The system SHALL provide a function to generate comprehensive AI-powered documentation for datasets and fields using various LLM providers, including structured metadata extraction, field-level descriptions, semantic type detection, and PII identification.

#### Scenario: Generate comprehensive documentation with structured metadata
- **WHEN** `ai.doc.generate()` is called with a dataset
- **THEN** the function generates documentation including:
  - **AND** dataset overview and purpose
  - **AND** structured metadata (title, keywords, geographic/temporal coverage, languages, data themes)
  - **AND** field-level descriptions with types and constraints
  - **AND** semantic type annotations (if available)
  - **AND** PII field identification (if enabled)
  - **AND** statistics and data quality metrics
  - **AND** sample data (optionally masked for PII)
- **AND** documentation is returned in the specified format (markdown, JSON, HTML, YAML, or text)

#### Scenario: Generate documentation with OpenAI
- **WHEN** `ai.doc.generate()` is called with `provider="openai"` and `model="gpt-4o-mini"`
- **THEN** the function generates documentation using OpenAI's API
- **AND** all structured metadata is extracted and included
- **AND** field-level descriptions are generated
- **AND** documentation is returned in the specified format

#### Scenario: Generate documentation with OpenRouter
- **WHEN** `ai.doc.generate()` is called with `provider="openrouter"`
- **THEN** the function generates documentation using OpenRouter's API
- **AND** provider selection works correctly
- **AND** API keys are handled securely
- **AND** all metadata extraction features work correctly

#### Scenario: Generate documentation with Ollama
- **WHEN** `ai.doc.generate()` is called with `provider="ollama"`
- **THEN** the function generates documentation using local Ollama instance
- **AND** local model execution works correctly
- **AND** network requirements are minimal
- **AND** all features work with local models

#### Scenario: Generate documentation with LMStudio
- **WHEN** `ai.doc.generate()` is called with `provider="lmstudio"`
- **THEN** the function generates documentation using LMStudio API
- **AND** local model execution works correctly
- **AND** all features work with local models

#### Scenario: Generate documentation with Perplexity
- **WHEN** `ai.doc.generate()` is called with `provider="perplexity"`
- **THEN** the function generates documentation using Perplexity API
- **AND** provider-specific features are utilized when available
- **AND** web search capabilities enhance documentation when applicable

### Requirement: Documentation Format Support
The system SHALL support multiple output formats for generated documentation, including markdown, JSON, HTML, YAML, and plain text.

#### Scenario: Generate markdown documentation
- **WHEN** `ai.doc.generate()` is called with `format="markdown"`
- **THEN** the function returns documentation in Markdown format
- **AND** markdown is well-formatted and readable
- **AND** includes appropriate headers, lists, code blocks, and tables
- **AND** includes structured metadata sections

#### Scenario: Generate JSON documentation
- **WHEN** `ai.doc.generate()` is called with `format="json"`
- **THEN** the function returns documentation in JSON format
- **AND** JSON structure is well-defined and parseable
- **AND** includes dataset and field metadata
- **AND** includes structured metadata (keywords, coverage, themes, etc.)
- **AND** includes statistics and usage information

#### Scenario: Generate HTML documentation
- **WHEN** `ai.doc.generate()` is called with `format="html"`
- **THEN** the function returns documentation in HTML format
- **AND** HTML is well-formed and styled appropriately
- **AND** includes proper document structure
- **AND** includes structured metadata sections

#### Scenario: Generate YAML documentation
- **WHEN** `ai.doc.generate()` is called with `format="yaml"`
- **THEN** the function returns documentation in YAML format
- **AND** YAML is well-formed and parseable
- **AND** includes all structured metadata
- **AND** includes schema and field information

#### Scenario: Generate plain text documentation
- **WHEN** `ai.doc.generate()` is called with `format="text"`
- **THEN** the function returns documentation in plain text format
- **AND** text is well-formatted and readable
- **AND** includes all documentation sections
- **AND** uses appropriate formatting for text output

### Requirement: Schema-Aware Documentation
The system SHALL use schema information to generate more accurate documentation.

#### Scenario: Documentation with schema context
- **WHEN** `ai.doc.generate()` is called with schema information
- **THEN** the function uses schema to understand field types and constraints
- **AND** generated documentation reflects schema information accurately
- **AND** field descriptions are more precise

#### Scenario: Documentation with sample data
- **WHEN** `ai.doc.generate()` is called with sample rows
- **THEN** the function uses samples to understand data patterns
- **AND** generated documentation includes examples
- **AND** documentation reflects actual data characteristics

### Requirement: Provider Abstraction
The system SHALL provide a unified interface for different LLM providers.

#### Scenario: Provider abstraction layer
- **WHEN** different providers are used
- **THEN** the API remains consistent across providers
- **AND** provider-specific configuration is handled transparently
- **AND** switching providers requires minimal code changes

#### Scenario: Provider configuration
- **WHEN** `ai.doc.generate()` is called with provider-specific options
- **THEN** options are passed to the appropriate provider
- **AND** invalid options are rejected with clear errors
- **AND** default options work for all providers

### Requirement: Error Handling
The system SHALL handle API errors and provider unavailability gracefully.

#### Scenario: Handle API errors
- **WHEN** an LLM provider API returns an error
- **THEN** the error is caught and reported clearly
- **AND** error messages include provider-specific context
- **AND** partial results are returned if available

#### Scenario: Handle missing dependencies
- **WHEN** `ai.doc.generate()` is called without AI dependencies installed
- **THEN** the function raises a clear error with installation instructions
- **AND** error message indicates which dependencies are missing
- **AND** graceful degradation is documented

#### Scenario: Handle rate limiting
- **WHEN** an LLM provider rate limits requests
- **THEN** the function implements appropriate retry logic
- **AND** rate limit errors are reported clearly
- **AND** retry delays respect rate limit headers

### Requirement: Cost and Performance
The system SHALL provide information about API usage and support cost optimization.

#### Scenario: Token usage reporting
- **WHEN** `ai.doc.generate()` completes
- **THEN** token usage information is available (if provider supports it)
- **AND** token counts help estimate costs
- **AND** usage information is included in return value

#### Scenario: Efficient prompt construction
- **WHEN** documentation is generated
- **THEN** prompts are constructed efficiently to minimize token usage
- **AND** unnecessary data is not included in prompts
- **AND** prompt engineering follows best practices

### Requirement: Integration with Schema Generation
The system SHALL integrate with schema generation to provide comprehensive documentation.

#### Scenario: Documentation with inferred schema
- **WHEN** `ai.doc.generate()` is called after schema inference
- **THEN** the function uses inferred schema for context
- **AND** documentation includes schema information
- **AND** field types and constraints are documented accurately

#### Scenario: Autodoc in analyze function
- **WHEN** `inspect.analyze()` is called with `autodoc=True`
- **THEN** AI documentation is generated as part of analysis
- **AND** documentation is included in analysis results
- **AND** integration is seamless

### Requirement: Structured Metadata Extraction
The system SHALL extract structured metadata from datasets including title, keywords, geographic coverage, temporal coverage, languages, and data themes.

#### Scenario: Extract keywords from field names and data
- **WHEN** documentation is generated for a dataset
- **THEN** keywords are extracted from field names and sample data
- **AND** keywords are ranked by frequency and relevance
- **AND** stopwords are filtered out
- **AND** keywords are included in documentation metadata

#### Scenario: Detect geographic coverage
- **WHEN** documentation is generated for a dataset with geographic fields
- **THEN** geographic coverage is detected (countries, regions, coordinates)
- **AND** country and region fields are identified
- **AND** coordinate fields (lat/lon) are detected
- **AND** geographic coverage is included in metadata

#### Scenario: Detect temporal coverage
- **WHEN** documentation is generated for a dataset with date/time fields
- **THEN** temporal coverage is detected (start date, end date, granularity)
- **AND** date ranges are calculated from sample data
- **AND** temporal granularity (date vs datetime) is determined
- **AND** temporal coverage is included in metadata

#### Scenario: Detect languages
- **WHEN** documentation is generated for a dataset with text fields
- **THEN** languages are detected from sample text data
- **AND** language detection uses appropriate libraries (langdetect)
- **AND** confidence scores are included
- **AND** multiple languages are supported

#### Scenario: Classify data themes
- **WHEN** documentation is generated for a dataset
- **THEN** data themes are classified based on field names and keywords
- **AND** theme classification uses standard taxonomies (e.g., EU data themes)
- **AND** theme URIs are included when available
- **AND** theme classification is included in metadata

### Requirement: Field-Level Documentation
The system SHALL generate individual field descriptions using AI, providing detailed documentation for each field in the dataset.

#### Scenario: Generate field descriptions
- **WHEN** `ai.doc.generate()` is called with `include_field_descriptions=True`
- **THEN** individual field descriptions are generated using AI
- **AND** field descriptions include purpose, format, and usage notes
- **AND** field descriptions are integrated into documentation output
- **AND** field descriptions use appropriate language

#### Scenario: Generate field descriptions for all providers
- **WHEN** field descriptions are requested
- **THEN** all supported providers can generate field descriptions
- **AND** provider abstraction handles field description generation
- **AND** field descriptions are consistent across providers

### Requirement: Semantic Type Detection
The system SHALL detect and annotate semantic types for fields using external tools like Metacrafter.

#### Scenario: Detect semantic types with Metacrafter
- **WHEN** `ai.doc.generate()` is called with `semantic_types=True` and Metacrafter is available
- **THEN** semantic types are detected for each field
- **AND** semantic type annotations include type name, URI, and confidence
- **AND** semantic types are included in field documentation
- **AND** semantic types enhance field descriptions

#### Scenario: Handle missing Metacrafter gracefully
- **WHEN** `ai.doc.generate()` is called with `semantic_types=True` but Metacrafter is not available
- **THEN** the function continues without semantic types
- **AND** a warning is logged (if logging enabled)
- **AND** documentation is still generated successfully

### Requirement: PII Detection and Masking
The system SHALL detect personally identifiable information (PII) in datasets and provide options to mask PII in sample data.

#### Scenario: Detect PII fields
- **WHEN** `ai.doc.generate()` is called with `pii_detect=True` and Metacrafter is available
- **THEN** PII fields are detected and identified
- **AND** PII field types are classified (email, phone, SSN, etc.)
- **AND** PII fields are marked in documentation
- **AND** PII detection confidence is included

#### Scenario: Mask PII in samples
- **WHEN** `ai.doc.generate()` is called with `pii_mask_samples=True` and PII fields are detected
- **THEN** PII values in sample data are masked (e.g., replaced with "***")
- **AND** masked samples are included in documentation
- **AND** original samples are not exposed
- **AND** PII masking is clearly indicated

#### Scenario: Handle missing PII detection gracefully
- **WHEN** `ai.doc.generate()` is called with `pii_detect=True` but PII detection is unavailable
- **THEN** the function continues without PII detection
- **AND** a warning is logged (if logging enabled)
- **AND** documentation is still generated successfully

### Requirement: Enhanced Statistics Integration
The system SHALL integrate comprehensive statistics from DuckDB-based analysis to enhance documentation quality.

#### Scenario: Include statistics in documentation
- **WHEN** `ai.doc.generate()` is called with `include_statistics=True` and DuckDB is available
- **THEN** statistics are computed using DuckDB
- **AND** statistics include uniqueness counts, total counts, and uniqueness percentages
- **AND** statistics are included in documentation output
- **AND** statistics enhance field descriptions

#### Scenario: Use statistics for better descriptions
- **WHEN** statistics are available
- **THEN** statistics are used to inform AI-generated descriptions
- **AND** high uniqueness fields are described appropriately
- **AND** low uniqueness fields are described appropriately
- **AND** statistics context improves description accuracy

### Requirement: Enhanced Prompt Engineering
The system SHALL use well-structured prompts that leverage all available context including schema, samples, statistics, and metadata.

#### Scenario: Construct comprehensive prompts
- **WHEN** documentation is generated
- **THEN** prompts include schema information (if available)
- **AND** prompts include sample data (if available)
- **AND** prompts include statistics (if available)
- **AND** prompts include extracted metadata
- **AND** prompts are optimized for token efficiency

#### Scenario: Use structured metadata in prompts
- **WHEN** structured metadata is extracted
- **THEN** metadata is included in prompts to improve context
- **AND** metadata helps generate more accurate descriptions
- **AND** metadata enhances dataset overview generation

### Requirement: Error Handling and Reliability
The system SHALL handle errors gracefully with retry logic, graceful degradation, and comprehensive error reporting.

#### Scenario: Retry on API failures
- **WHEN** an LLM provider API call fails with a retryable error
- **THEN** the function retries the request with exponential backoff
- **AND** retry attempts are limited (e.g., 3 attempts)
- **AND** retry delays respect rate limit headers
- **AND** final failure is reported clearly

#### Scenario: Graceful degradation
- **WHEN** optional features fail (e.g., Metacrafter, statistics)
- **THEN** the function continues without those features
- **AND** documentation is still generated successfully
- **AND** warnings are logged for missing features
- **AND** core functionality is not compromised

#### Scenario: Handle rate limiting
- **WHEN** an LLM provider rate limits requests
- **THEN** the function implements appropriate retry logic
- **AND** rate limit errors are reported clearly
- **AND** retry delays respect rate limit headers
- **AND** rate limit information is included in error messages

#### Scenario: Handle timeouts
- **WHEN** an LLM provider request times out
- **THEN** the function retries with appropriate timeout handling
- **AND** timeout errors are reported clearly
- **AND** timeout configuration is respected

### Requirement: Integration with Operations
The system SHALL integrate seamlessly with other IterableData operations including stats, schema, and inspect.

#### Scenario: Integration with stats.compute()
- **WHEN** `ai.doc.generate()` is called
- **THEN** statistics from `ops.stats.compute()` are used when available
- **AND** statistics enhance documentation quality
- **AND** statistics are included in output
- **AND** integration is seamless

#### Scenario: Integration with schema.infer()
- **WHEN** `ai.doc.generate()` is called with `include_schema=True`
- **THEN** schema from `ops.schema.infer()` is used
- **AND** schema information enhances field descriptions
- **AND** schema constraints are documented
- **AND** integration is seamless

