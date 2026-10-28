## ADDED Requirements

### Requirement: Optional Accelerated Gzip Backend

The gzip codec SHALL use ISA-L (`isal`) for compression when it is installed and SHALL fall back to the standard library otherwise. Output SHALL remain a valid gzip stream readable by the standard library.

#### Scenario: Writing gzip with isal installed

- **WHEN** a user writes `out.jsonl.gz` with `isal` installed
- **THEN** the codec SHALL compress with ISA-L
- **AND** `gzip.open("out.jsonl.gz")` SHALL read back the same records

#### Scenario: isal not installed

- **WHEN** `isal` is not importable
- **THEN** the codec SHALL compress with the standard-library `gzip` module without warnings
