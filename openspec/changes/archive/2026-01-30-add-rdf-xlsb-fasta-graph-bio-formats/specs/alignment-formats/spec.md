## ADDED Requirements

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
