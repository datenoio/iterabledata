# Change: Convert full-load readers to lazy/batch iteration

## Why

Several formats materialize the entire file or table during `reset()`, contradicting the project's core memory-efficiency constraint (`openspec/project.md`): Shapefile builds all features into a list (`shapefile.py:95-101`), Arrow/Feather calls `feather.read_table()` (`arrow.py:50`), Lance materializes the full scan via `scanner.to_table()` (`lance.py:137-139`), Delta calls `to_pyarrow_table()` (`delta.py:48`), Iceberg calls `scan.to_arrow().to_pylist()` (`iceberg.py:84`), Hudi calls `to_pandas()` (`hudi.py:85-86`), and XLSX opens workbooks without `read_only=True` (`xlsx.py:51`). On large inputs these formats exhaust memory even though users iterate row by row.

## What Changes

- Shapefile: iterate `shapefile.Reader` lazily instead of building `self.features`.
- Arrow/Feather: use a record-batch reader (`pyarrow.ipc` / `RecordBatchFileReader`) instead of `read_table()` at open.
- Lance: iterate `scanner.to_batches()` instead of `to_table()`.
- Delta/Iceberg/Hudi: use scan batch iterators (`DeltaTable.to_pyarrow_dataset().to_batches()`, PyIceberg scan batches, Hudi batch APIs where available); document residual full-load paths where the underlying library offers none.
- XLSX: pass `read_only=True` to `load_workbook()` in the main read path (already used in `list_tables()` at `xlsx.py:117`).
- `read_bulk()` on converted formats yields true batches from the underlying columnar API where available.
- Update each converted format's `is_streaming()` declaration (coordinates with change `update-streaming-capability-truth`).

## Impact

- Affected specs: `datatype-implementation`
- Affected code: `iterable/datatypes/shapefile.py`, `arrow.py`, `lance.py`, `delta.py`, `iceberg.py`, `hudi.py`, `xlsx.py`; tests for each
- Behavior preserved (same records, same order where the format guarantees order); memory profile changes from O(file) to O(batch).
