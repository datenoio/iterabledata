# alignment-formats Specification

## Purpose
TBD - created by archiving change add-rdf-xlsb-fasta-graph-bio-formats. Update Purpose after archive.
## Requirements
### Requirement: SAM Format Reading
The system SHALL support reading SAM (Sequence Alignment/Map) text files using pysam, yielding one record per alignment.

#### Scenario: Read SAM file with automatic detection
- **WHEN** user opens a file with extension `.sam` via `open_iterable`
- **THEN** the system selects the SAM iterable and yields alignment records as dicts (or dict-like rows)

#### Scenario: Read valid SAM content
- **WHEN** reading a valid SAM file (header optional, then tab-separated alignment lines)
- **THEN** each yielded record SHALL represent one alignment with fields accessible as defined by the implementation (e.g. query name, reference, position, CIGAR, sequence, quality)
- **AND** records SHALL be streamed so that large files do not require loading all alignments into memory

#### Scenario: Missing pysam dependency for SAM
- **WHEN** pysam is not installed and user attempts to read a SAM file
- **THEN** the system SHALL raise an ImportError with a message instructing to install the alignment or bio extra (e.g. `pip install iterabledata[alignment]`)

### Requirement: BAM Format Reading
The system SHALL support reading BAM (binary SAM) files using pysam, yielding one record per alignment.

#### Scenario: Read BAM file with automatic detection
- **WHEN** user opens a file with extension `.bam` via `open_iterable`
- **THEN** the system selects the BAM iterable and yields alignment records as dicts (or dict-like rows)

#### Scenario: Read valid BAM content
- **WHEN** reading a valid BAM file
- **THEN** each yielded record SHALL represent one alignment with fields accessible as defined by the implementation
- **AND** records SHALL be streamed; the implementation SHALL use pysam's iterator interface where appropriate to avoid loading the entire file

#### Scenario: Missing pysam dependency for BAM
- **WHEN** pysam is not installed and user attempts to read a BAM file
- **THEN** the system SHALL raise an ImportError with install instructions for the alignment or bio extra

#### Scenario: BAM index optional
- **WHEN** reading a BAM file with or without an index (`.bai`)
- **THEN** the system SHALL support sequential iteration in both cases
- **AND** indexed access (e.g. by region) MAY be supported as an extension and is not required for this requirement

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

