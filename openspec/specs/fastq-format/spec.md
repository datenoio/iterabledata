# fastq-format Specification

## Purpose
TBD - created by archiving change add-rdf-xlsb-fasta-graph-bio-formats. Update Purpose after archive.
## Requirements
### Requirement: FASTQ Format Reading
The system SHALL support reading FASTQ (sequence with quality) files, yielding one record per read with id, sequence, quality, and optional description.

#### Scenario: Read FASTQ file with automatic detection
- **WHEN** user opens a file with extension `.fq` or `.fastq` via `open_iterable`
- **THEN** the system selects the FASTQ iterable and yields one dict per read

#### Scenario: Read valid FASTQ content
- **WHEN** reading a valid FASTQ file (four-line blocks: id, sequence, plus, quality)
- **THEN** each yielded record SHALL contain at least id, sequence, and quality (e.g. keys `id`, `sequence`, `quality`, and optionally `description`)
- **AND** records SHALL be streamed so that large files do not require loading all reads into memory

#### Scenario: FASTQ with multiple reads
- **WHEN** reading a FASTQ file containing multiple four-line blocks
- **THEN** the system SHALL yield one record per read in order
- **AND** each record SHALL include the quality string corresponding to that read

#### Scenario: Handle malformed or empty FASTQ
- **WHEN** opening an empty file or a file with incomplete blocks
- **THEN** the system SHALL raise a clear error or yield only complete records as defined by the implementation
- **AND** the system SHALL NOT crash on truncated input when documented behavior is defined

