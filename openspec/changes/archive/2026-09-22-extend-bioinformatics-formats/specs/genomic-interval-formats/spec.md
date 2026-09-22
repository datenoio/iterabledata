## ADDED Requirements

### Requirement: Streaming BED Support

The system SHALL read and write BED3 through BED12 plus deterministic extra columns as streaming text records while preserving BED's 0-based, half-open coordinate convention.

#### Scenario: Read BED record

- **WHEN** a valid BED line is read
- **THEN** the row SHALL include `chrom`, `chromStart`, and `chromEnd`
- **AND** present optional BED fields SHALL use documented names and types
- **AND** coordinates SHALL NOT be silently converted to another convention

#### Scenario: BED12 block validation

- **WHEN** a BED12 record contains block count, sizes, and starts
- **THEN** their counts and values SHALL be validated for consistency
- **AND** malformed records SHALL follow the configured error policy

#### Scenario: BED round trip

- **WHEN** supported BED records, track/browser lines, and extra columns are written and reopened
- **THEN** logical fields, coordinate values, ordering, and supported headers SHALL round-trip

### Requirement: Streaming GFF3 and GTF Support

The system SHALL read and write GFF3 and GTF records with the nine canonical columns, 1-based closed coordinates, structured attributes, and documented directive/comment preservation.

#### Scenario: Read GFF3 feature

- **WHEN** a valid GFF3 feature line is read
- **THEN** the row SHALL include `seqid`, `source`, `type`, `start`, `end`, `score`, `strand`, `phase`, and `attributes`
- **AND** coordinates SHALL remain 1-based and closed

#### Scenario: Parse GTF attributes

- **WHEN** a GTF record is read
- **THEN** its attribute syntax SHALL be parsed according to the GTF profile
- **AND** lossless mode SHALL retain the original attribute text for round trip

#### Scenario: Directives and comments

- **WHEN** GFF3/GTF input contains directives or comments
- **THEN** they SHALL be preserved as iterable metadata or typed records according to the documented option
- **AND** their handling SHALL not require full-file loading

#### Scenario: GFF3 FASTA tail

- **WHEN** a GFF3 file reaches a `##FASTA` section
- **THEN** the iterable SHALL follow its documented stop, metadata, or delegated FASTA policy
- **AND** it SHALL NOT parse sequence lines as feature rows

### Requirement: Genomic Interval Compression and Errors

BED, GFF3, and GTF SHALL compose with supported streaming codecs and provide clear malformed-record and missing-dependency behavior.

#### Scenario: Read gzip-compressed BED or GFF

- **WHEN** a `.bed.gz`, `.gff3.gz`, or `.gtf.gz` file is opened
- **THEN** records SHALL stream through the existing gzip codec
- **AND** memory SHALL remain bounded by codec and record/batch buffers

#### Scenario: Truncated or malformed record

- **WHEN** a record lacks required columns or contains invalid coordinates/attributes
- **THEN** the format error SHALL identify the filename and line number when available
- **AND** the configured error policy SHALL be applied
