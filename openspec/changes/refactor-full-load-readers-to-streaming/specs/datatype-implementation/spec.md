## ADDED Requirements

### Requirement: Batch-Iterating Readers for Columnar and Record Sources

Datatype implementations whose underlying libraries expose batch or record iterators (Arrow/Feather, Lance, Delta, Iceberg, Shapefile, XLSX) SHALL read through those incremental APIs rather than materializing the whole file or table during `reset()`. Where an underlying library offers no incremental API, the implementation SHALL document the full-load behavior in its class docstring and declare `is_streaming()` as `False`.

#### Scenario: Shapefile iterates lazily

- **WHEN** a large shapefile is opened and the first record is read
- **THEN** only the shapes required so far SHALL have been parsed
- **AND** peak memory SHALL be bounded by record size, not feature count

#### Scenario: Columnar formats read by batch

- **WHEN** an Arrow, Lance, Delta, or Iceberg source is iterated
- **THEN** data SHALL be fetched via the library's batch iterator
- **AND** `read_bulk()` SHALL map to the underlying batch API where available

#### Scenario: Records are unchanged by the conversion

- **WHEN** an existing fixture is read with the batch-iterating implementation
- **THEN** the yielded records SHALL be identical (content and, where the format guarantees it, order) to the previous full-load implementation
