## Context

Zarr stores contain groups and arrays rather than one natural stream of dictionaries. Arrays may be dense, structured, scalar, chunked along arbitrary dimensions, and backed by local or remote stores.

## Goals / Non-Goals

- Goals:
  - Read v2/v3 stores with bounded chunk memory.
  - Provide deterministic row mappings and table discovery.
  - Support useful local/cloud selection and compatible writes.
- Non-Goals:
  - Flatten every multidimensional array into scalar cells by default.
  - Hide all Zarr storage/backend differences.
  - Make Zarr a core dependency.

## Decisions

### Format identity and source types

The canonical id is `zarr`. Local `.zarr` directories and recognized stores are path/store based, not arbitrary file-like streams. Cloud URLs use storage options and a compatible Zarr/fsspec store.

### Array selection and tables

`list_tables()` returns array paths. `iterableargs={"array": "path"}` selects one; a store with exactly one array may select it automatically. Group paths alone are not row sources.

### Row mapping

Iteration uses `axis=0` by default. Structured arrays yield one dictionary per element with named fields. Dense 1-D arrays yield `{"index": i, "value": value}`. Dense N-D arrays yield `{"index": i, "values": slice}` with values converted according to an explicit `array_mode` (`python`, `numpy`, or metadata-only where supported). Scalar arrays yield one record.

### Selection and chunks

Optional `slice`, `columns`/fields, and batch/chunk hints are applied before conversion. Chunk boundaries guide I/O, but returned bulk sizes follow the IterableData contract.

### Writes

Writers require explicit array/schema/shape or infer compatible structure from the first batch. Append is supported only along a declared appendable axis. Writes are flushed by chunks; incompatible later shapes/dtypes fail clearly.

## Risks / Trade-offs

- Row mapping may not suit every scientific use case. Mitigation: explicit modes and documentation.
- Zarr v2/v3/backend APIs evolve. Mitigation: supported version range and versioned fixtures.
- Object arrays/codecs may execute unsafe deserialization. Mitigation: reject unsafe object codecs by default and document trust requirements.

## Migration Plan

Add as an experimental format, stabilize read/table/selection behavior first, then enable writes after round-trip and cloud-store tests pass.

## Open Questions

- Should `numpy` array values be allowed in rows by default or only through an explicit advanced mode?
- Which v3 codecs/stores are required for initial stable status?
