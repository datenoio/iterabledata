## ADDED Requirements

### Requirement: Codec Arguments in Conversion

`convert()` and `bulk_convert()` SHALL accept `codecargs` for the source and `tocodecargs` for the destination and SHALL pass them to the codec that opens each file.

#### Scenario: Compression level for the output

- **WHEN** a user calls `convert("a.csv", "b.jsonl.gz", tocodecargs={"compression_level": 1})`
- **THEN** the gzip codec SHALL write the output with compression level 1

### Requirement: Bulk Conversion Parameter Parity

`bulk_convert()` SHALL accept every per-file conversion parameter that `convert()` accepts, including `use_native_batch`, `selection` and `strict_native`, and SHALL forward them to each file conversion.

#### Scenario: Selection in bulk conversion

- **WHEN** a user calls `bulk_convert("in/*.parquet", "out/", to_ext="jsonl", selection={"columns": ["id"]})`
- **THEN** every output file SHALL contain only the `id` field
