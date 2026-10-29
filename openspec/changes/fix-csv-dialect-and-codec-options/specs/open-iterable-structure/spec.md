## ADDED Requirements

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
