## ADDED Requirements

### Requirement: Prompt-shaped cookbook examples
The project SHALL provide a cookbook of short runnable examples under `examples/cookbook/` that
match common LLM generation prompts (read a file, convert formats, inspect a dataset). Cookbook
scripts SHALL use canonical public imports and context managers.

#### Scenario: Cookbook directory present
- **WHEN** a user looks under `examples/cookbook/`
- **THEN** they find at least one script each for reading, converting, and inspecting
- **AND** a README that lists the prompt each script answers

#### Scenario: Cookbook uses public imports
- **WHEN** CI inspects Python files under `examples/cookbook/`
- **THEN** those files import `open_iterable` from `iterable` or `convert` from `iterable.convert`
- **AND** they do not import `open_iterable` from `iterable.helpers.detect`

#### Scenario: Cookbook scripts run against fixtures
- **WHEN** the cookbook smoke test runs
- **THEN** the read and inspect examples complete successfully against a committed CSV fixture
