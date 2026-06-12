## ADDED Requirements

### Requirement: FASTA Format Reading
The system SHALL support reading FASTA (sequence) files, yielding one record per sequence with id, description, and sequence fields.

#### Scenario: Read FASTA file with automatic detection
- **WHEN** user opens a file with extension `.fa`, `.fasta`, `.fna`, or `.faa` via `open_iterable`
- **THEN** the system selects the FASTA iterable and yields one dict per sequence

#### Scenario: Read valid FASTA content
- **WHEN** reading a valid FASTA file
- **THEN** each yielded record SHALL contain at least an identifier and sequence (e.g. keys `id`, `sequence`, and optionally `description`)
- **AND** records SHALL be streamed so that large files do not require loading all sequences into memory

#### Scenario: FASTA with multiple sequences
- **WHEN** reading a FASTA file containing multiple sequences (multiple header lines)
- **THEN** the system SHALL yield one record per sequence in order
- **AND** each record SHALL be self-contained with its header and sequence data

#### Scenario: Handle malformed or empty FASTA
- **WHEN** opening an empty file or a file with no valid FASTA headers
- **THEN** the system SHALL yield no records or raise a clear error as defined by the implementation
- **AND** the system SHALL NOT crash on empty input
