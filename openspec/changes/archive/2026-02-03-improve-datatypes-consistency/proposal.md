# Change: Improve Data Types Consistency

## Why
Validation hooks are ignored in `write`/`write_bulk` for most datatypes (only CSV applies them), so data can be written without validation. SQLite bulk read and TopoJSON write have correctness and performance gaps.

## What Changes
- Enforce `_apply_validation_hooks` in all datatype `write` and `write_bulk` implementations (e.g. json, parquet, sqlite, topojson).
- Use `cursor.fetchmany()` in `SQLiteIterable.read_bulk` for efficient bulk reading.
- Make `TopoJSONIterable.write_bulk` produce a valid Topology JSON object (single `{"type":"Topology",...}`) instead of concatenated objects.
- Add tests that validation hooks are invoked for these formats.
- Improve type hints for data rows where applicable.

## Impact
- Affected specs: validation-consistency (new), sqlite-optimization (new), topojson-format (ADDED requirement).
- Affected code: `iterable/datatypes/*.py` (json, parquet, sqlite, topojson, and others from audit), tests.

## Summary
Align datatype implementations for consistent validation hook usage, SQLite bulk read optimization, and TopoJSON write correctness.

## Goals
1. **Enforce Validation**: Ensure `_apply_validation_hooks` is called in all `write` and `write_bulk` implementations.
2. **Optimize SQLite**: Use `fetchmany` for efficient bulk reading in `SQLiteIterable`.
3. **Fix TopoJSON**: Correct the TopoJSON write implementation to produce valid Topology structure.
4. **Standardize Types**: Improve type hints for data rows.

## Non-Goals
- Rewriting the entire type system (focused changes only).
- Adding new data formats (focus on improving existing ones).
