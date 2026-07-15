## ADDED Requirements

### Requirement: Staged, Behavior-Preserving Entry Points

The core entry points (`open_iterable`, `convert`, `bulk_convert`, `Pipeline.run`) SHALL be organized into independently testable stages while preserving their public signatures and observable behavior. Each function's cyclomatic complexity SHALL be reduced below radon grade C.

#### Scenario: Public behavior is unchanged

- **WHEN** the existing test suite runs against the refactored entry points
- **THEN** all previously passing tests SHALL still pass
- **AND** the public signatures of `open_iterable`, `convert`, and `bulk_convert` SHALL be unchanged

#### Scenario: Stages are independently testable

- **WHEN** a developer tests format detection, source validation, or engine configuration for `open_iterable`
- **THEN** each stage SHALL be callable and assertable without executing the entire function

#### Scenario: Complexity is bounded

- **WHEN** radon analyzes the refactored functions
- **THEN** each SHALL report a cyclomatic grade of C or better
