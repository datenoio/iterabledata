# validation-consistency Specification

## Purpose
TBD - created by archiving change improve-datatypes-consistency. Update Purpose after archive.
## Requirements
### Requirement: Validation hooks MUST be applied during write operations
All data type implementations MUST apply configured validation hooks in their `write` and `write_bulk` methods.

#### Scenario: Writing invalid data to JSON
Given a JSONIterable configured with a validation hook that rejects a specific record
When I write that record using `write`
Then the record should be silently skipped (or raise error depending on policy)
And the validation hook should have been called

#### Scenario: Writing invalid data to Parquet
Given a ParquetIterable configured with a validation hook
When I write a bulk of records using `write_bulk`
Then only valid records should be written to the file

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

