## 1. Provider abstraction
- [x] 1.1 Add `generate_structured(prompt, json_schema, ...)` to `LLMProvider` with json_schema/json_object fallback
- [x] 1.2 Implement `generate_structured` for OpenAI-compatible providers (OpenAI, OpenRouter, LMStudio, Azure, Perplexity, generic)
- [x] 1.3 Honor `LLM_PROVIDER`/`LLM_BASE_URL`/`LLM_API_KEY`/`LLM_DEFAULT_MODEL` env vars in `get_provider()`
- [x] 1.4 Add generic "openai-compatible" provider driven by `LLM_BASE_URL`

## 2. Models
- [x] 2.1 Add per-block Pydantic models in `iterable/ai/models.py` (general, schema fields, quality, examples, statistics, codebook, block envelope)

## 3. Sampling and stats
- [x] 3.1 Add `iterable/ai/sampling.py` with size-based strategy and `MAX_ROWS_SAMPLING`
- [x] 3.2 Extend `ops.stats.compute()` with `null_fraction`, `top_values`, `is_dictionary` (`DICT_THRESHOLD`)

## 4. File metadata + multi-table
- [x] 4.1 Add `iterable/ai/fileinfo.py` (file_name, file_size, sha256, format, encoding, record_count, table_count)
- [x] 4.2 Support XLS/XLSX `tables=` selection and per-table schema blocks via `list_tables()`

## 5. Progress + logging
- [x] 5.1 Add `iterable/ai/progress.py` with `Stage` enum and progress callback contract
- [x] 5.2 Emit per-stage structured JSON logs (job_id, stage, duration_ms, token usage) via `OperationContext`

## 6. Blocks + API
- [x] 6.1 Add `iterable/ai/blocks.py` block registry and v1 block generators returning `{markdown, data}`
- [x] 6.2 Add `doc.generate_blocks()` returning `{source, blocks, full_document_markdown}` with context + progress
- [x] 6.3 Batch schema-block LLM calls when columns > 100 and merge `fields[]`
- [x] 6.4 Refactor `doc.generate()` to delegate while preserving signature/return types

## 7. Tools, tests, docs
- [x] 7.1 Extend `tools/_core.generate_documentation` to expose `blocks`/`context`
- [x] 7.2 Add provider-mocked tests for blocks, structured output, sampling tiers, stats enrichment, progress, multi-table
- [x] 7.3 Update `docs/docs/api/` AI pages, ai-integration skill, and `examples/ai`
