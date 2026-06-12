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

