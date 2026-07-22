# Change: Add Write Support for Delta Lake, Iceberg, and Hudi

## Why

Delta Lake, Apache Iceberg, and Apache Hudi are already readable in IterableData but all three raise `WriteNotSupportedError`. Lance, Vortex, and Paimon file formats already offer write paths. Enabling writes for the classic lakehouse trio removes a sharp usability cliff for ETL and conversion workflows that target those tables.

## What Changes

- Implement bounded write/append (and create-where-supported) paths for `DeltaIterable`, `IcebergIterable`, and `HudiIterable`.
- Flip format descriptors from `writable=False` to writable with accurate `write_memory` / maturity metadata.
- Preserve existing read behavior; document supported write modes per backend (`deltalake`, `pyiceberg`, `hudi`).
- Add round-trip tests, clear errors for unsupported operations (e.g. complex upserts if deferred), and docs updates.

## Impact

- Affected specs: `delta-format` (new), `iceberg-format` (new), `hudi-format` (new)
- Affected code: `iterable/datatypes/{delta,iceberg,hudi}.py`, format registry writable flags, tests, format docs, README capability notes
- Dependencies: reuse existing `lakehouse` extra packages; may require minimum version bumps if write APIs need newer clients
- **Not breaking** for readers; writers that previously always failed will begin succeeding for supported modes
