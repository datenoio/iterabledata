# Change: Add runnable examples for ops, database reading, ingest, pipeline, validate, and convert

**Status: Approved. Implementation complete.**

## Why

Users need runnable, copy-paste examples for high-level features (ops, ingest, db reading, pipeline, validate, convert). The project has `examples/` with some MongoDB/Elasticsearch/converter content but lacks structured examples for ops (filter, inspect, stats, schema, transform), ingest (`to_db`), database reading (`open_iterable` with `engine=`), pipeline, and validate. A single OpenSpec proposal will define the requirement and tasks; implementation will add example scripts and READMEs under `examples/` in relevant subdirs.

## What Changes

- Add OpenSpec spec delta for an **examples** capability: the project SHALL provide runnable example scripts for ops, database reading, ingest, pipeline, validate, and convert, under `examples/` in subdirs aligned to feature areas.
- Add under `examples/`:
  - **examples/ops/** – filter (expression, search), inspect (count, head, tail), stats (compute, frequency), schema (infer, to_json_schema), transform (head, tail, sample, select, slice).
  - **examples/ingest/** – `to_db` examples for PostgreSQL and SQLite (and optionally MongoDB) with README.
  - **examples/db/** – reading from databases via `open_iterable(..., engine=...)` for PostgreSQL, SQLite, MySQL with README.
  - **examples/pipeline/** – pipeline run with a process function and optional progress.
  - **examples/validate/** – validate.iterable with rules (e.g. email, required) and mode/stats.
  - **examples/convert/** – README documenting convert usage (existing converter/convert.py retained).
- Each subdir SHALL include a README describing the feature and how to run the examples.
- No API or behavior changes; documentation and example assets only.

## Impact

- Affected specs: new **examples** capability (documentation/examples).
- Affected code: none (new files under `examples/` only).
- Improves onboarding and reduces support burden for ops, ingest, db reading, pipeline, validate, and convert.
