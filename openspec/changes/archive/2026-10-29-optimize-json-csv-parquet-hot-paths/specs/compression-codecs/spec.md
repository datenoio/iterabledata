## ADDED Requirements

### Requirement: Optional Accelerated Gzip Backend

When ISA-L (`isal`) is installed, the gzip codec SHALL compress with it at the levels where its ratio matches zlib's (levels 1-2, the `fast` profile) and SHALL keep zlib at other levels unless the `backend="isal"` codec option requests ISA-L. Without ISA-L it SHALL use the standard library. Output SHALL remain a valid gzip stream readable by the standard library.

#### Scenario: Writing gzip with isal installed

- **WHEN** a user writes `out.jsonl.gz` with `codecargs={"profile": "fast"}` and `isal` installed
- **THEN** the codec SHALL compress with ISA-L
- **AND** `gzip.open("out.jsonl.gz")` SHALL read back the same records

#### Scenario: isal not installed

- **WHEN** `isal` is not importable
- **THEN** the codec SHALL compress with the standard-library `gzip` module without warnings
