## Context

The row API and bulk API currently maintain separate consumption state in Arrow and Parquet. Parquet write buffering stops after writer creation, so row writes generate nearly one row group per row. JSONL bulk reading performs successful `tell()` calls per line, conversion recomputes totals at each callback interval, and some writers retain all records until close.

## Goals / Non-Goals

- Goals:
  - Make row and bulk operations semantically interchangeable.
  - Keep read and write memory bounded by configured batch limits where the backend supports incremental I/O.
  - Remove measured hot-path regressions without weakening parse-error context.
  - Protect physical output structure as well as elapsed time.
- Non-Goals:
  - Introduce a new public native-batch protocol; that belongs to `add-native-batch-conversion`.
  - Force naturally whole-document formats to stream.
  - Change the row dictionary contract.

## Decisions

### One consumption state per iterable

Each iterable will own one backend iterator and one remainder buffer. `read()` consumes one record from that state; `read_bulk(n)` consumes up to `n` records from the same state. Remainders will use a deque or an immutable batch plus index, not `list.pop(0)`.

### Separate read batch size from Parquet row-group size

Parquet will retain a write buffer after schema creation. `row_group_size` will control flush boundaries independently of read `batch_size`. Schema normalization happens once per flushed group. Dictionary encoding and compression settings remain configurable.

### Totals are immutable conversion context

Conversion will compute an estimated total at most once, before the write loop, and pass the cached value to progress reporting. A totals implementation must either use metadata/an independent stream or restore state; it must never consume the active cursor. Codec-wrapped line totals will count decompressed records or return unknown.

### Error context must be cheap on successful records

Readers will maintain line numbers and offsets incrementally where possible. Exact byte offsets may be omitted when unavailable; successful records will not perform an expensive seek/tell solely for a potential future error.

### Whole-output writers are explicit

Arrow and Lance will flush at configured batch limits using persistent writers/backend append operations. If Vortex cannot append safely with its supported API, it will remain whole-output and be declared/documented as such rather than advertised as bounded.

## Risks / Trade-offs

- Changing Parquet group boundaries can change file size and scan characteristics. Mitigation: structural tests plus round-trip and compatibility tests.
- A single cursor requires careful reset behavior. Mitigation: interleaving and reset conformance tests.
- Lazy error context may provide no byte offset on some text wrappers. Mitigation: retain filename, line number, and original line, and document when byte offsets are unavailable.
- Writer flushing fixes schema after the first batch. Mitigation: retain existing schema-adaptation policy and fail clearly on incompatible later batches.

## Migration Plan

1. Add failing semantic and structural tests.
2. Replace dual cursor/remainder state.
3. Repair writer buffering and totals caching.
4. Optimize text-reader offset tracking.
5. Establish new performance baselines only after correctness tests pass.

Rollback is limited to reverting the internal cursor/buffer implementations; public signatures do not change.

## Open Questions

- Should the default Parquet `row_group_size` be row-count based only, or also support an approximate byte target?
- Does the supported Vortex backend expose a safe incremental writer in every supported version?
