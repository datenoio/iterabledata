## ADDED Requirements

### Requirement: Optional Dependencies Skip, Not Fail

The test suite SHALL skip tests that require an uninstalled optional dependency rather than failing or erroring at collection. Test modules SHALL NOT import optional format/codec classes at module top level in a way that breaks collection when the dependency is absent.

#### Scenario: Base environment collects cleanly

- **WHEN** the suite runs in an environment with no optional extras installed
- **THEN** there SHALL be zero collection errors
- **AND** tests needing missing dependencies SHALL be reported as skipped

#### Scenario: Optional test skips with reason

- **WHEN** a test requires a package that is not installed
- **THEN** it SHALL be skipped with a reason naming the missing dependency
- **AND** SHALL NOT be reported as a failure or error

### Requirement: Fixture Symlink Integrity Guard

The test session SHALL fail fast with an actionable message if `tests/testdata` is not a symlink to the committed `tests/fixtures` directory, so that broken checkouts do not produce large numbers of misleading failures.

#### Scenario: Broken symlink is detected early

- **WHEN** `tests/testdata` exists as a regular file instead of a symlink
- **THEN** session startup SHALL raise a clear error explaining how to restore the symlink
- **AND** SHALL NOT proceed to run tests that would fail spuriously

### Requirement: Default Run Excludes Long-Running Tests

The default test invocation SHALL exclude `stress`, `slow`, `benchmark`, and `integration` marked tests, and long-running tests SHALL carry their own timeouts so the default run completes without tripping the global timeout.

#### Scenario: Default run avoids the 10GB stress test

- **WHEN** the default `pytest` invocation runs
- **THEN** the 10 GB streaming stress test SHALL NOT run
- **AND** the run SHALL NOT abort due to the global timeout
