# Spec Delta: validation-consistency

## ADDED Requirements

### Requirement: Validation hooks on all writable formats

Every writable format SHALL apply the standard write-time validation hooks in
its `write()` and `write_bulk()` paths.

#### Scenario: Registry-driven coverage

- **WHEN** the conformance test enumerates formats with `writable=True`
- **THEN** each format's write path invokes `_apply_validation_hooks`, and the
  test fails for any format that bypasses it

#### Scenario: Default behavior unchanged

- **WHEN** no validator is configured for a writable format
- **THEN** writing behaves exactly as before (no-op policy)
