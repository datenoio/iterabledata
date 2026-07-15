## ADDED Requirements

### Requirement: Truthful Streaming Declaration

Every datatype implementation SHALL declare its memory behavior explicitly via `is_streaming()`: implementations whose read path is genuinely incremental (peak memory bounded by record/batch size, not file size) SHALL return `True`, and implementations that materialize the whole file or table during `reset()` or iteration SHALL return `False` and document this in the class docstring. The capability API SHALL report this declaration instead of `None` for built-in formats whose behavior is known.

#### Scenario: Streaming reader declares True

- **WHEN** `get_format_capabilities()` is queried for a format whose reader is incremental (e.g. ORC, Avro, BSON, MessagePack, PCAP, SQLite)
- **THEN** the `streaming` capability SHALL be `True`
- **AND** `is_streaming()` on an instance SHALL return `True`

#### Scenario: Full-load reader declares False

- **WHEN** `get_format_capabilities()` is queried for a format that materializes the entire input (e.g. Arrow/Feather, Lance, Delta, Iceberg, Hudi, Shapefile, CBOR, YAML, TOML)
- **THEN** the `streaming` capability SHALL be `False`
- **AND** the class docstring SHALL state that the whole file or table is loaded into memory

#### Scenario: New formats must declare deliberately

- **WHEN** the streaming-declaration conformance test runs against a registered built-in format missing from the reviewed allowlist
- **THEN** the test SHALL fail
- **AND** the failure message SHALL instruct the author to classify the format's memory behavior
