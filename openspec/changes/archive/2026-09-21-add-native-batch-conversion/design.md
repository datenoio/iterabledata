## Context

The universal `dict` row is valuable for format interoperability, but it is an expensive interchange for Arrow-native sources and destinations. A conversion can currently perform `RecordBatch → list[dict] → Table`, losing zero/low-copy opportunities and creating Python objects for unselected columns.

## Goals / Non-Goals

- Goals:
  - Preserve native batches between compatible endpoints.
  - Push projection/filter/slice requests into capable backends.
  - Keep row semantics and fallback behavior identical.
  - Avoid making PyArrow a core dependency.
- Non-Goals:
  - Replace `read()`, `read_bulk()`, or the dictionary iterator.
  - Promise zero-copy for incompatible schemas/backends.
  - Translate arbitrary Python callables into every backend query language.

## Decisions

### Optional protocol

Batch-capable iterables will expose an optional protocol such as `iter_native_batches(request)` and writable destinations an optional `write_native_batch(batch)`. The concrete interchange may be PyArrow `RecordBatch` for Arrow-compatible extras or a registered adapter for other backends. Core code discovers support without importing PyArrow.

### Selection request

A typed request will carry optional columns, predicate/filter, table/variable, row range, multidimensional slice, and batch-size hints. Backends declare which fields they can honor. Unsupported parts either trigger row fallback or a clear strict-mode error; they are never silently ignored.

### Conversion path selection

`convert()` uses the native path only when source/destination adapters are compatible and requested operations do not require per-row flattening, validation hooks, or callbacks. Otherwise it uses the existing row path. Metrics count logical rows on both paths.

### Schema and ownership

Batches are immutable from the conversion layer's perspective. Destinations may cast/reorder to a negotiated schema. The producer owns batch lifetime until the consumer call returns; consumers must retain safely if writes are asynchronous.

### Initial backend scope

Phase 1 covers Parquet, Arrow IPC/Feather v2, and ORC where supported. Phase 2 covers Lance, Delta, Iceberg, HDF5/NetCDF selection, and DuckDB/SQLite adapters where their installed backend exposes batches.

## Risks / Trade-offs

- Backend batch APIs and schemas differ. Mitigation: small adapter registry and explicit compatibility negotiation.
- Native and row paths may diverge semantically. Mitigation: equivalence tests with nulls, nested values, dates, and schema changes.
- Predicates can be backend-specific or unsafe. Mitigation: structured predicates first; raw expressions remain trusted APIs with documented boundaries.

## Migration Plan

1. Define protocol, request, adapter, and fallback semantics.
2. Add path-selection diagnostics and equivalence tests.
3. Implement Parquet/Arrow/ORC source and destination adapters.
4. Add lakehouse/scientific adapters incrementally.
5. Benchmark and document where the native path is selected.

## Open Questions

- Should the advanced method names be public immediately or remain experimental under `iterable.native`?
- Which structured predicate representation can be shared without adding a heavy core dependency?
