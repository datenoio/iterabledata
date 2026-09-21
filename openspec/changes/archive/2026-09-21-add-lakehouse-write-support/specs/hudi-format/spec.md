## ADDED Requirements

### Requirement: Hudi Write Support

The system SHALL add write support for Apache Hudi when the pinned Python client exposes a reliable append or copy-on-write write path; if that path is not viable, the change SHALL document deferral and keep Hudi read-only rather than shipping a broken writer.

#### Scenario: Supported append round trip

- **WHEN** Hudi writes are implemented and supported records are written then read back
- **THEN** the logical field values SHALL match for the supported table/write mode subset

#### Scenario: Explicit deferral

- **WHEN** evaluation shows no stable Hudi Python write API for the pinned dependency
- **THEN** tasks/docs SHALL record the deferral
- **AND** Hudi SHALL remain read-only with `WriteNotSupportedError` unchanged in behavior

#### Scenario: Descriptor accuracy

- **WHEN** Hudi write support is enabled or deferred
- **THEN** the format descriptor `writable` flag SHALL match the shipped behavior
