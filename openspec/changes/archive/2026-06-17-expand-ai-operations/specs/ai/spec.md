## ADDED Requirements

### Requirement: Anthropic Provider Support
The system SHALL support Anthropic Claude models as a first-class LLM provider for AI operations.

#### Scenario: Generate documentation with Anthropic
- **WHEN** `ai.doc.generate()` is called with `provider="anthropic"` and a valid API key
- **THEN** the function generates documentation using the Anthropic Messages API
- **AND** the provider abstraction API remains consistent with OpenAI providers

#### Scenario: Missing Anthropic dependency
- **WHEN** `provider="anthropic"` is requested without the `anthropic` package installed
- **THEN** a clear `ImportError` is raised with install instructions

### Requirement: Google Gemini Provider Support
The system SHALL support Google Gemini models as a first-class LLM provider for AI operations.

#### Scenario: Generate documentation with Gemini
- **WHEN** `ai.doc.generate()` is called with `provider="gemini"` and valid credentials
- **THEN** the function generates documentation using the Google GenAI API
- **AND** the provider abstraction API remains consistent

### Requirement: Azure OpenAI Provider Support
The system SHALL support Azure OpenAI deployments via the provider abstraction.

#### Scenario: Generate documentation with Azure OpenAI
- **WHEN** `ai.doc.generate()` is called with `provider="azure"` and Azure endpoint configuration
- **THEN** the function uses the Azure OpenAI client
- **AND** authentication follows `AZURE_OPENAI_*` environment conventions

### Requirement: AI Conversion Planning
The system SHALL provide a function to produce declarative conversion plans between formats using
catalog metadata and optional LLM reasoning.

#### Scenario: Plan CSV to Parquet conversion
- **WHEN** `ai.plan_conversion("data.csv", "data.parquet")` is called
- **THEN** the function returns a JSON-serializable plan with recommended steps and capability warnings
- **AND** does not perform the conversion unless explicitly invoked separately

#### Scenario: Plan warns on read-only target
- **WHEN** `plan_conversion()` targets a read-only format for write
- **THEN** the plan includes an explicit warning in the response

### Requirement: AI Transform Suggestions
The system SHALL suggest data transforms as declarative JSON specs, not executable code.

#### Scenario: Suggest transforms for a goal
- **WHEN** `ai.suggest_transform(iterable, goal="normalize email addresses")` is called
- **THEN** the function returns a transform spec with whitelisted operations
- **AND** does not return arbitrary Python source code

#### Scenario: Apply transform spec safely
- **WHEN** `ops.transform.apply_spec(iterable, spec)` is called with a valid spec
- **THEN** the function applies only whitelisted operations
- **AND** rejects unknown operation types with a clear error

### Requirement: Natural Language Filter Translation
The system SHALL translate natural language or simple DSL filter expressions into a safe AST
executable by `ops.filter`, without passing raw SQL to engines.

#### Scenario: Translate simple filter
- **WHEN** `ai.translate_filter("age > 30 AND country = 'US'", schema=sch)` is called
- **THEN** the function returns a validated filter AST
- **AND** `ops.filter` can apply the AST to an iterable

#### Scenario: Reject unsafe filter input
- **WHEN** `translate_filter()` receives SQL injection patterns or multi-statement input
- **THEN** the function raises a validation error
- **AND** does not execute arbitrary expressions

### Requirement: Prompt Template Versioning
The system SHALL store versioned prompt templates for AI operations in package resources.

#### Scenario: Load documentation prompt template
- **WHEN** `doc.generate()` constructs a prompt
- **THEN** it uses a template from `iterable/ai/prompts/`
- **AND** template changes are testable via snapshot or hash tests

### Requirement: Optional Documentation Caching
The system SHALL support opt-in caching of `doc.generate()` results to reduce cost and latency.

#### Scenario: Cache hit
- **WHEN** `doc.generate(..., cache=True)` is called twice with identical inputs
- **THEN** the second call returns the cached result without calling the LLM API
- **AND** `cache=False` remains the default for backward compatibility

### Requirement: AI Integration Testing
The system SHALL provide integration tests for LLM providers behind an explicit pytest marker and
environment guards.

#### Scenario: Integration tests skipped without credentials
- **WHEN** `pytest -m integration` runs without API keys configured
- **THEN** provider integration tests are skipped
- **AND** default CI does not require live API access
