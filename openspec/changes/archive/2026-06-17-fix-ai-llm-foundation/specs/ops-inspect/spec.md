## MODIFIED Requirements

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
- **AND** does not include `documentation` or `documentation_meta` keys

#### Scenario: Analyze with autodoc enabled
- **WHEN** `inspect.analyze()` is called with `autodoc=True` and AI dependencies available
- **THEN** the function performs structure analysis
- **AND** calls `iterable.ai.doc.generate()` using the analyzed context
- **AND** includes `documentation` in the result (generated text or structured doc payload)
- **AND** includes `documentation_meta` with provider, model, format, and usage info when available
- **AND** merges AI field descriptions into field metadata when `include_field_descriptions` is enabled

#### Scenario: Analyze with autodoc and missing AI dependencies
- **WHEN** `inspect.analyze()` is called with `autodoc=True` and AI optional dependencies are not installed
- **THEN** the function raises `ImportError` with installation instructions for `iterabledata[ai]`
- **AND** does not return a partial result silently
