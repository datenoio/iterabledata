# Tasks: Add examples for ops, database reading, ingest, pipeline, validate, convert

**Status: Approved. Implementation complete.**

## 1. OpenSpec and scaffolding

- [x] 1.1 Add `openspec/changes/add-examples-for-features/` with proposal.md, tasks.md.
- [x] 1.2 Add spec delta `specs/examples/spec.md` with ADDED requirement for runnable examples.
- [x] 1.3 Run `openspec validate add-examples-for-features --strict` and fix any issues.

## 2. Examples: ops

- [x] 2.1 Create `examples/ops/` directory.
- [x] 2.2 Add `examples/ops/filter_example.py` (filter_expr, search).
- [x] 2.3 Add `examples/ops/inspect_example.py` (count, head, tail).
- [x] 2.4 Add `examples/ops/stats_example.py` (compute, frequency).
- [x] 2.5 Add `examples/ops/schema_example.py` (infer, to_json_schema).
- [x] 2.6 Add `examples/ops/transform_example.py` (head, tail, sample_rows, select, slice_rows).
- [x] 2.7 Add `examples/ops/README.md` describing ops and how to run each script.

## 3. Examples: ingest

- [x] 3.1 Create `examples/ingest/` directory (if not exists).
- [x] 3.2 Add `examples/ingest/to_db_postgresql.py` using `to_db` with dbtype=postgresql.
- [x] 3.3 Add `examples/ingest/to_db_sqlite.py` using `to_db` with dbtype=sqlite.
- [x] 3.4 Add `examples/ingest/README.md` describing ingest and how to run examples.

## 4. Examples: database reading (db)

- [x] 4.1 Create `examples/db/` directory.
- [x] 4.2 Add `examples/db/read_postgresql.py` (open_iterable with engine=postgres).
- [x] 4.3 Add `examples/db/read_sqlite.py` (open_iterable with engine=sqlite).
- [x] 4.4 Add `examples/db/read_mysql.py` (open_iterable with engine=mysql).
- [x] 4.5 Add `examples/db/README.md` describing db reading and how to run examples.

## 5. Examples: pipeline and validate

- [x] 5.1 Create `examples/pipeline/` directory.
- [x] 5.2 Add `examples/pipeline/run_pipeline.py` (pipeline with process_func, optional progress).
- [x] 5.3 Add `examples/pipeline/README.md`.
- [x] 5.4 Create `examples/validate/` directory.
- [x] 5.5 Add `examples/validate/validate_example.py` (validate.iterable with rules).
- [x] 5.6 Add `examples/validate/README.md`.

## 6. Examples: convert

- [x] 6.1 Add or update `examples/convert/README.md` (or `examples/converter/README.md`) documenting convert usage and referencing existing convert.py.

## 7. Validation

- [x] 7.1 Ensure all new scripts run without errors when given the required inputs (or skip gracefully with clear message).
- [x] 7.2 Re-run `openspec validate add-examples-for-features --strict`.
