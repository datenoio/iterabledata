# Change: Optimize Core Format I/O Hot Paths

## Why

The performance review found path-dependent behavior in core formats: Parquet row writes created thousands of tiny row groups, Arrow and Parquet repeated rows when `read()` and `read_bulk()` were mixed, JSONL bulk reads were slower than row iteration, conversion totals rescanned inputs, and several writers buffered the whole output. These defects undermine the iterator API's performance and bounded-memory promises.

## What Changes

- Keep Parquet writes buffered to a configurable row-group boundary after schema creation.
- Make `read()` and `read_bulk()` share one logical cursor for Arrow, Parquet, and every custom bulk reader.
- Remove avoidable per-record offset work from JSONL and CSV success paths while preserving useful parse errors.
- Compute conversion totals once without consuming or repeatedly scanning the source, including codec-wrapped inputs.
- Bound Arrow and Lance write buffers; explicitly classify backends such as Vortex when whole-output buffering is unavoidable.
- Add paired row/bulk, structural, and peak-memory regression checks.

## Dependencies

- Archive `add-performance-regression-gate`, `refactor-full-load-readers-to-streaming`, `update-codec-streaming`, and `update-streaming-capability-truth` before implementation so their completed deltas are current specs.
- Coordinate descriptor fields with `unify-format-capability-metadata`.

## Impact

- Affected specs: `datatype-implementation`, `convert`, `performance-regression`
- Affected code: `iterable/datatypes/{parquet,arrow,jsonl,csv,lance,vortex}.py`, `iterable/helpers/read_ahead.py`, `iterable/helpers/utils.py`, `iterable/convert/core.py`
- Affected tests: performance regression, benchmarks, memory profiling, and format-specific cursor/write tests
- Compatibility: public row and bulk signatures remain unchanged; output chunking and Parquet physical layout become deterministic and efficient
