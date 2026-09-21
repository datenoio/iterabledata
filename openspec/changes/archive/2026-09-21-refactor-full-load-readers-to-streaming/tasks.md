## 1. File formats

- [x] 1.1 Shapefile: replace feature-list materialization with lazy iteration over `shapefile.Reader`
- [x] 1.2 Arrow/Feather: switch `reset()` to a record-batch reader; keep `read_bulk()` on the batch path
- [x] 1.3 XLSX: use `read_only=True` in the main `reset()` workbook load

## 2. Lakehouse formats

- [x] 2.1 Lance: iterate `scanner.to_batches()`
- [x] 2.2 Delta: read via `to_pyarrow_dataset().to_batches()`
- [x] 2.3 Iceberg: use scan batch iteration instead of `to_arrow().to_pylist()`
- [x] 2.4 Hudi: use batch APIs where the library allows; document any remaining full-load path

## 3. Consistency and tests

- [x] 3.1 Update `is_streaming()` declarations for all converted formats
- [x] 3.2 Round-trip/read-equivalence tests: converted formats yield identical records to the previous implementation on existing fixtures
- [x] 3.3 Memory-bound test on a generated large fixture for at least Shapefile and Arrow (skip without optional deps)
- [x] 3.4 Run full test suite and lint
