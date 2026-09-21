## ADDED Requirements

### Requirement: TAR Multi-File Container Reading

The system SHALL provide a `tar` container format that iterates the data members of a TAR archive (including `.tar`, `.tar.gz`/`.tgz`, `.tar.bz2`, `.tar.xz`, and `.tar.zst`), detecting each member's format and yielding its records. Members SHALL be read as in-memory streams; the container SHALL NOT extract files to disk.

#### Scenario: Iterate all members

- **WHEN** a tarball containing CSV and JSONL members is opened via `open_iterable()`
- **THEN** iteration SHALL yield the records of each data member in archive order
- **AND** each record SHALL be tagged with the originating member name

#### Scenario: Select a specific member

- **WHEN** the user passes an `iterableargs` member selector (exact name or glob)
- **THEN** only matching members SHALL be read
- **AND** non-matching members SHALL be skipped

#### Scenario: Compressed tarballs

- **WHEN** a `.tar.gz` or `.tar.zst` archive is opened
- **THEN** the container SHALL transparently decompress and iterate members
- **AND** behavior SHALL match the equivalent uncompressed tarball

### Requirement: TAR Path-Traversal Safety

The `tar` container SHALL NOT trust member paths: members with absolute paths or `..` path-traversal components SHALL be rejected or skipped, and no member SHALL be written to the filesystem during reading.

#### Scenario: Reject traversal member

- **WHEN** a TAR archive contains a member named `../evil` or an absolute path
- **THEN** the container SHALL skip or reject that member with a clear error
- **AND** SHALL NOT write any file outside of memory
