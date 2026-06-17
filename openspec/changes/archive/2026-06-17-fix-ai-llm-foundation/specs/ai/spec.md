## MODIFIED Requirements

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

#### Scenario: Autodoc in analyze function
- **WHEN** `inspect.analyze()` is called with `autodoc=True` and AI dependencies are available
- **THEN** AI documentation is generated as part of analysis via `ai.doc.generate()`
- **AND** `documentation` and `documentation_meta` are included in the analysis result
- **AND** integration is seamless and non-silent

#### Scenario: Autodoc missing dependencies
- **WHEN** `inspect.analyze()` is called with `autodoc=True` and AI dependencies are not installed
- **THEN** a clear `ImportError` is raised with install instructions
- **AND** the error is not swallowed

## ADDED Requirements

### Requirement: AI Specification Purpose
The `ai` capability SHALL document its purpose as providing LLM-powered dataset understanding
and documentation generation integrated with IterableData's schema, statistics, and inspect
operations, with a unified provider abstraction and graceful degradation for optional features.

#### Scenario: Purpose documented in spec
- **WHEN** a contributor or agent reads `openspec/specs/ai/spec.md`
- **THEN** the Purpose section describes dataset documentation, metadata extraction, and inspect integration
- **AND** the Purpose is not a placeholder

### Requirement: OpenSpec Conformance Testing
The system SHALL include automated tests that verify key `ai` spec scenarios using mocked LLM
providers, so implementation drift is caught in CI.

#### Scenario: Core doc generation scenario tested
- **WHEN** CI runs the AI conformance test suite
- **THEN** tests cover `doc.generate()` markdown and JSON output paths with a mocked provider
- **AND** token usage metadata is asserted when available

#### Scenario: Autodoc integration scenario tested
- **WHEN** CI runs inspect + AI integration tests
- **THEN** `inspect.analyze(autodoc=True)` is verified to call documentation generation
- **AND** missing-dependency behavior is verified to raise `ImportError`
