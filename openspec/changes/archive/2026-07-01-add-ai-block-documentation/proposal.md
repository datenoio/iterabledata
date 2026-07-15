# Change: Block-based AI documentation with structured output, context, and progress hooks

## Why
The dataset-documentation service (separate repo) requires iterabledata to generate
documentation as independent, machine-readable **blocks** (general, schema, quality,
examples, statistics, codebook) instead of a single markdown blob, with structured JSON
output, user-supplied context, in-process per-stage progress hooks, and per-stage
structured logging. The current `ai.doc.generate()` produces one opaque document and has
no progress/observability hooks, no JSON-Schema-driven output, and no context parameter.

## What Changes
- Add `ai.doc.generate_blocks()` returning `{source, blocks{name:{markdown,data}}, full_document_markdown}`.
- Add a block registry (`iterable/ai/blocks.py`) with v1 blocks: `general`, `schema`,
  `quality`, `examples`, `statistics`, `codebook`. `lineage` and `geo_coverage` are
  registered but deferred (return a not-implemented marker).
- Add `generate_structured()` to the LLM provider abstraction (JSON Schema where supported,
  `json_object` + Pydantic validation fallback) and per-block Pydantic models.
- Add a `context` parameter (title, description, tags, territory, source_url, card metadata)
  threaded into prompts.
- Add in-process progress hooks (`iterable/ai/progress.py`) with a `Stage` enum and a
  `progress` callback, plus per-stage structured JSON logging (job_id, stage, duration_ms,
  token usage).
- Add a size-based sampling strategy (`iterable/ai/sampling.py`): small/medium/large tiers
  driven by `MAX_ROWS_SAMPLING`.
- Extend `ops.stats.compute()` with optional `null_fraction`, `top_values`, and
  `is_dictionary` (via `DICT_THRESHOLD`).
- Add file metadata helpers (size, sha256, encoding, record_count, table_count) and
  XLS/XLSX multi-table documentation (`tables=` selection, per-table schema block).
- Honor `LLM_PROVIDER` / `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_DEFAULT_MODEL` env vars and
  add a generic OpenAI-compatible provider.
- Batch schema-block LLM calls when columns > 100.
- Keep `ai.doc.generate()` fully backward compatible (delegates to the block engine).

## Impact
- Affected specs: `ai`, `ops-stats`
- Affected code: `iterable/ai/doc.py`, `iterable/ai/providers.py`, `iterable/ai/models.py`,
  new `iterable/ai/blocks.py`, `iterable/ai/progress.py`, `iterable/ai/sampling.py`,
  `iterable/ai/fileinfo.py`, `iterable/ops/stats.py`, `iterable/tools/_core.py`,
  docs and examples.
- Out of scope: service infrastructure (FastAPI/Celery/Redis/PostgreSQL/web UI/Prometheus/
  Docker/webhooks/portal handlers). Deferred: geo/lineage blocks, SQLite docs, DOCX/PDF export.
