## ADDED Requirements

### Requirement: CRAM Format Reading

The system SHALL support sequential reading of CRAM alignment files using `pysam`, yielding the same logical alignment row shape as SAM/BAM and preserving bounded-memory iteration.

#### Scenario: Read CRAM with automatic detection

- **WHEN** a user opens a `.cram` file through `open_iterable()`
- **THEN** the CRAM iterable SHALL be selected
- **AND** records SHALL use the documented SAM/BAM-compatible alignment fields

#### Scenario: Sequential CRAM without index

- **WHEN** a valid CRAM file has no CRAI index and sequential iteration is requested
- **THEN** records SHALL still be yielded in file order
- **AND** the complete file SHALL not be materialized in memory

#### Scenario: CRAM requires a reference

- **WHEN** decoding requires a reference and the configured `reference_filename` is absent or invalid
- **THEN** the iterable SHALL raise a clear resource error naming the missing reference requirement
- **AND** it SHALL NOT download a reference automatically

#### Scenario: Missing pysam dependency

- **WHEN** CRAM is opened without `pysam`
- **THEN** an `ImportError` SHALL name the alignment/bio extra

### Requirement: Alignment Format Row Consistency

SAM, BAM, and CRAM SHALL use one documented alignment-to-row mapping for equivalent records.

#### Scenario: Equivalent alignment in three encodings

- **WHEN** equivalent SAM, BAM, and CRAM fixtures are read
- **THEN** their logical row fields and value meanings SHALL match
- **AND** encoding-specific metadata MAY be exposed separately without changing core fields
