# Change: Expand AI operations — providers, planning, and safe transforms

## Why

`iterable.ai` today only generates documentation. Integration guides document Anthropic Claude and
Google Gemini patterns, but those providers are not first-class in `iterable.ai.providers`.
Agents need declarative conversion plans and transform suggestions—not `exec()` on generated
Python. Phase 4 expands AI to planning and safe transform specs, adds native Anthropic/Gemini/Azure
providers, NL→filter translation to a safe AST, integration tests, and prompt assets.

## What Changes

- **ADDED**: `AnthropicProvider`, `GeminiProvider`, `AzureOpenAIProvider` in `iterable/ai/providers.py`.
- **ADDED**: `ai.plan_conversion(source, target, **kwargs)` — returns declarative conversion plan JSON.
- **ADDED**: `ai.suggest_transform(iterable, goal, **kwargs)` — returns transform spec dict, not executable code.
- **ADDED**: `ai.translate_filter(expression, **kwargs)` — NL or DSL to safe filter AST executed by `ops.filter`.
- **ADDED**: Versioned prompt templates in `iterable/ai/prompts/`.
- **ADDED**: Optional response caching for `doc.generate()` (content-hash keyed).
- **ADDED**: `@pytest.mark.integration` live provider tests (env-guarded) and VCR-style fixtures.
- **MODIFIED**: Default cloud-provider examples use `redact_for_llm` when sending samples.

Backward compatible. New functions are additive; existing `doc.generate()` unchanged.

## Impact

- Affected specs: `ai` (major expansion), `ops-filter` (safe NL filter integration)
- Affected code: `iterable/ai/`, `iterable/ops/filter.py`, `pyproject.toml`, `tests/test_ai*.py`,
  `docs/docs/api/ai.md`, `docs/integrations/`
- Depends on: `fix-ai-llm-foundation`, `add-llm-catalog` (plans use catalog)
- Optional synergy: `add-agent-tool-surfaces` (new tools wrap new AI functions)
