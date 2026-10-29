## ADDED Requirements

### Requirement: Stable Subpackage Bindings

Attributes of the top-level `iterable` package that share a name with a subpackage SHALL refer to that subpackage.

#### Scenario: Patching an AI provider by string path

- **WHEN** a test patches `"iterable.ai.providers.get_provider"`
- **THEN** the patch SHALL replace the function that `iterable.ai.doc` calls

### Requirement: Complete Runtime Resources in Distributions

Every non-Python file that the package loads at runtime SHALL be included in the wheel and the source distribution, and the release smoke test SHALL load each such resource from the installed wheel.

#### Scenario: AI prompt templates after installation

- **WHEN** the wheel is installed into a clean environment
- **THEN** `importlib.resources` SHALL find every `iterable/ai/prompts/*.txt` file
- **AND** `iterable.ai.prompts.load_prompt()` SHALL succeed for each template
