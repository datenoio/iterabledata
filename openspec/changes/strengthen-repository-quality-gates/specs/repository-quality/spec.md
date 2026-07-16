## ADDED Requirements

### Requirement: Truthful Blocking Type Checks

Every Mypy command configured as a required CI check SHALL pass. The project SHALL maintain an explicit, package-scoped ratchet that prevents new typing errors and expands zero-error coverage toward the public `py.typed` contract.

#### Scenario: Core Mypy job runs

- **WHEN** the required core Mypy command executes
- **THEN** it SHALL report zero errors
- **AND** CI SHALL fail if any configured core file regresses

#### Scenario: Historically untyped package changes

- **WHEN** a file in a package with recorded historical debt is modified
- **THEN** the change SHALL NOT increase that package's error count
- **AND** newly added public signatures SHALL be typed

### Requirement: Enforced Static Quality Baselines

The repository SHALL maintain reviewed blocking thresholds for Ruff formatting/lint, actionable documentation style, dead code, and complexity. Existing debt SHALL be cleared or recorded explicitly before a tool becomes blocking.

#### Scenario: Static checks run in CI

- **WHEN** a pull request changes Python code
- **THEN** all required static checks SHALL run with the same configuration available locally
- **AND** failures SHALL identify the file and rule/threshold

#### Scenario: Complexity hotspot is refactored

- **WHEN** an E/F-rated function is changed to reduce complexity
- **THEN** focused behavior tests SHALL preserve its externally observable results and failures

### Requirement: Complete and Current Repository Guidance

Published format documentation SHALL contain verified content rather than template placeholders, and repository status documents SHALL describe current format counts, checks, OpenSpec state, and contributor workflow.

#### Scenario: Format documentation check

- **WHEN** documentation validation scans format pages
- **THEN** known template markers such as placeholder use cases/descriptions SHALL be absent
- **AND** each page SHALL identify installation, capabilities, memory behavior, and limitations

#### Scenario: Completed OpenSpec work

- **WHEN** an OpenSpec change is fully implemented and approved for archival
- **THEN** it SHALL be archived through the standard workflow
- **AND** overlapping future proposals SHALL use the archived current spec as their base
