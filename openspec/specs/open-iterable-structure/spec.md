# open-iterable-structure Specification

## Purpose
TBD - created by archiving change refactor-core-entry-points. Update Purpose after archive.
## Requirements
### Requirement: Staged, Behavior-Preserving Entry Points

The core entry points (`open_iterable`, `convert`, `bulk_convert`, `Pipeline.run`) SHALL be organized into independently testable stages while preserving their public signatures and observable behavior. Each function's cyclomatic complexity SHALL be reduced below radon grade C.

#### Scenario: Public behavior is unchanged

- **WHEN** the existing test suite runs against the refactored entry points
- **THEN** all previously passing tests SHALL still pass
- **AND** the public signatures of `open_iterable`, `convert`, and `bulk_convert` SHALL be unchanged

#### Scenario: Stages are independently testable

- **WHEN** a developer tests format detection, source validation, or engine configuration for `open_iterable`
- **THEN** each stage SHALL be callable and assertable without executing the entire function

#### Scenario: Complexity is bounded

- **WHEN** radon analyzes the refactored functions
- **THEN** each SHALL report a cyclomatic grade of C or better

### Requirement: Explicit Format Preserves Compression

When `open_iterable()` receives an explicit `format`, it SHALL still apply the compression codec detected from the file's last extension. An explicit `codec` hint SHALL select the codec for names without a codec extension.

#### Scenario: Gzipped CSV with an explicit format

- **WHEN** a user opens `x.csv.gz` with `iterableargs={"format": "csv"}`
- **THEN** the file SHALL be decompressed with the gzip codec
- **AND** the reader SHALL return the CSV records

#### Scenario: ZIP archive whose name has no inner format

- **WHEN** a user opens `data.zip` containing JSON Lines with `iterableargs={"format": "jsonl"}`
- **THEN** the reader SHALL return the JSON Lines records

#### Scenario: Explicit codec hint

- **WHEN** a user opens `data.bin` with `iterableargs={"format": "jsonl", "codec": "gz"}`
- **THEN** the file SHALL be decompressed with the gzip codec

