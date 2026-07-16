# Change: Add Native-Batch Conversion and Selection Pushdown

## Why

Columnar, lakehouse, database, and scientific readers often obtain native batches, immediately convert them to `list[dict]`, and later rebuild a native table in the destination writer. Conversion also reads every source row individually. This preserves the row API but discards columnar throughput, copies data unnecessarily, and prevents consistent projection/slice pushdown.

## What Changes

- Add an optional advanced native-batch read/write protocol without changing the row iterator contract.
- Let `convert()` transfer compatible batches directly when no row-only transform requires materialization.
- Standardize projection, filter, table/variable, row-range, and slice requests for backends that support them.
- Implement adapters first for Parquet/Arrow/ORC and selected lakehouse/scientific formats, with safe row fallback.
- Preserve validation, flattening, progress, error, and schema semantics across both paths.

## Dependencies

- Implement after `optimize-format-io-hot-paths` establishes correct shared cursor semantics.
- Implement after or alongside `unify-format-capability-metadata`, which declares native-batch and selection support.

## Impact

- Affected specs: `native-batch-io`, `convert`
- Affected code: `BaseIterable`/optional protocols, conversion core, columnar/lakehouse/scientific datatypes, destination writers
- Compatibility: row APIs remain supported; the batch API is additive and optional; PyArrow remains an optional dependency
