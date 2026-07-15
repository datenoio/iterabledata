## Context
A separate dataset-documentation service consumes iterabledata as its parsing and
LLM-documentation engine. It needs block-level, machine-readable output, the ability to
pass dataset-card/user context, progress callbacks for a job-based UI, and structured logs
for observability. This change adds those library primitives without pulling any service
infrastructure (FastAPI/Celery/Redis/DB/web) into the library.

## Goals / Non-Goals
- Goals:
  - Block-based generation with `{markdown, data}` per block and an assembled document.
  - Structured Output via JSON Schema with a safe fallback.
  - User `context` parameter, in-process progress hooks, per-stage structured logs.
  - Size-based sampling, richer stats (null fraction, top values, dictionary flag).
  - Backward-compatible `doc.generate()`.
- Non-Goals (this change):
  - HTTP API, task queue, persistence, web UI, Prometheus, Docker, webhooks, portal handlers.
  - Geo blocks (`geo_coverage`), `lineage`, SQLite docs, DOCX/PDF export (registered/deferred).

## Decisions
- Decision: A block registry maps block name -> generator callable. Each generator takes a
  shared `BlockContext` (schema, samples, stats, file metadata, user context, provider) and
  returns `{"markdown": str, "data": dict}`. This keeps blocks independent and testable.
- Decision: Structured output uses `provider.generate_structured(prompt, json_schema)`.
  OpenAI-compatible providers try `response_format={"type":"json_schema",...}`, then fall
  back to `{"type":"json_object"}`, then to plain text + best-effort JSON extraction; the
  result is validated against the block's Pydantic model.
- Decision: Progress is a plain callback `Callable[[ProgressEvent], None]` (no async, no
  queue). Stages mirror the spec lifecycle. Logging reuses `OperationContext` and the
  existing structured logging framework.
- Decision: Sampling tiers by file size: `<1MB` schema + first N; `1-20MB` first N + N
  random; `>20MB` schema + stats only. N defaults from `MAX_ROWS_SAMPLING` (50/20). Random
  rows use reservoir sampling (DuckDB SAMPLE may be wired later).
- Decision: `ops.stats.compute()` gains opt-in flags (`top_n`, `dict_threshold`,
  `include_top_values`) and always-present `null_fraction` so existing callers keep working.

## Risks / Trade-offs
- LLM provider variance in structured-output support → graceful fallback + validation.
- Token blow-up on wide schemas → batch by 50 columns and merge.
- Backward compatibility of `generate()` → covered by delegating and keeping return shapes.

## Migration Plan
- Additive change; `generate()` keeps its signature. New `generate_blocks()` is opt-in.

## Open Questions
- None blocking; geo/portal/export remain explicitly deferred.
