## 1. Correct cursor semantics

- [x] 1.1 Add a shared row/bulk cursor helper or equivalent internal state using deque/indexed remainders.
- [x] 1.2 Migrate Parquet and Arrow to the shared consumption state.
- [ ] 1.3 Add interleaved `read()`/`read_bulk()`/reset conformance tests for all custom bulk readers.

## 2. Repair write buffering

- [x] 2.1 Add a Parquet `row_group_size` write option distinct from read `batch_size`.
- [x] 2.2 Keep Parquet records buffered after schema creation and flush complete groups efficiently.
- [x] 2.3 Add row-group count, output-size sanity, schema-alignment, row/bulk equivalence, and bounded-memory tests.
- [x] 2.4 Flush Arrow and Lance writers at configured bounds using a persistent writer or backend append operation.
- [x] 2.5 Verify whether Vortex can write incrementally; otherwise declare and document whole-output buffering.

## 3. Optimize text and progress paths

- [x] 3.1 Remove successful per-line `tell()` overhead from JSONL bulk reads and profile the equivalent CSV path.
- [x] 3.2 Preserve line number/original-line diagnostics and conditionally provide byte offsets.
- [x] 3.3 Compute conversion totals once and pass the cached estimate to all progress updates.
- [x] 3.4 Make line totals correct for compressed inputs and non-destructive for streams.

## 4. Regression coverage and documentation

- [x] 4.1 Add paired CSV/JSONL/Parquet/Arrow row-versus-bulk workloads at representative sizes.
- [x] 4.2 Add peak-memory and physical-layout assertions for bounded writers.
- [x] 4.3 Update format/performance documentation with batch and row-group tuning guidance.
- [ ] 4.4 Run Ruff, focused tests, the full suite, and the performance regression gate.
- [ ] 4.5 Regenerate committed baselines only when the reviewed implementation intentionally changes them.
