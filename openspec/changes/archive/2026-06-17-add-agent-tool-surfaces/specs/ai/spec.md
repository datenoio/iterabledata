## ADDED Requirements

### Requirement: Validated JSON Documentation Output
The system SHALL support optional Pydantic validation of `ai.doc.generate()` JSON responses so
agents receive schema-stable payloads.

#### Scenario: Validate JSON output
- **WHEN** `doc.generate(..., format="json", validate_output=True)` completes successfully
- **THEN** the returned dict conforms to the `DocumentationResult` model
- **AND** validation errors are reported clearly when the model response is malformed

#### Scenario: Validation disabled by default
- **WHEN** `doc.generate()` is called without `validate_output`
- **THEN** behavior remains backward compatible with existing JSON dict responses

#### Scenario: Documented response model
- **WHEN** API documentation for `iterable.ai` is consulted
- **THEN** the JSON response fields are documented with types matching the Pydantic models
