## ADDED Requirements

### Requirement: WebDataset Sample Iteration

The system SHALL support reading WebDataset TAR shards as an iterable of sample records, where members sharing a key are grouped into one dictionary keyed by member suffix.

#### Scenario: Read WebDataset shard

- **WHEN** a WebDataset TAR shard is opened with `format="webdataset"` (or equivalent detected id)
- **THEN** the system SHALL yield one record per sample key
- **AND** each record SHALL include a sample key field and suffix-mapped payloads

#### Scenario: Codec-composed shard

- **WHEN** a WebDataset shard uses a supported compression codec (e.g. `.tar.gz`)
- **THEN** detection SHALL compose codec handling with WebDataset sample grouping

#### Scenario: Default TAR behavior unchanged

- **WHEN** a TAR archive is opened as plain `tar` without WebDataset mode
- **THEN** the system SHALL continue to iterate archive members individually

#### Scenario: Partial trailing sample group

- **WHEN** a shard ends with an incomplete sample group
- **THEN** the system SHALL apply the documented behavior (error or partial yield)
- **AND** SHALL NOT silently drop the condition without documentation
