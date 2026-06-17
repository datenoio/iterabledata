## 1. Native LLM providers

- [x] 1.1 Implement `AnthropicProvider` using `anthropic` SDK
- [x] 1.2 Implement `GeminiProvider` using `google-genai` SDK
- [x] 1.3 Implement `AzureOpenAIProvider` extending OpenAI client with Azure config
- [x] 1.4 Register providers in `get_provider()` with env var conventions (`ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `AZURE_OPENAI_*`)
- [x] 1.5 Add optional extras to `pyproject.toml`: `anthropic`, `google-genai`
- [x] 1.6 Update `docs/docs/api/ai.md` and integration guides to reference native providers
- [x] 1.7 Add mocked unit tests per provider in `tests/test_ai_providers.py`

## 2. Conversion planning

- [x] 2.1 Create `iterable/ai/plan.py` with `plan_conversion(source, target, **kwargs)`
- [x] 2.2 Use `catalog.describe_format()` for capability warnings (read-only target, missing extra)
- [x] 2.3 Return JSON plan: steps, recommended kwargs, codec handling, estimated considerations
- [x] 2.4 Add prompt template `iterable/ai/prompts/plan_conversion.txt`
- [x] 2.5 Add `tests/test_ai_plan.py`
- [x] 2.6 Add example `examples/ai/plan_conversion.py`

## 3. Transform suggestions (declarative)

- [x] 3.1 Create `iterable/ai/suggest.py` with `suggest_transform(iterable, goal, **kwargs)`
- [x] 3.2 Define `TransformSpec` Pydantic model and allowed operation vocabulary
- [x] 3.3 Implement `ops.transform.apply_spec(iterable, spec)` executing whitelisted ops
- [x] 3.4 Add prompt template `iterable/ai/prompts/suggest_transform.txt`
- [x] 3.5 Add round-trip tests: spec generation (mocked) + deterministic apply
- [x] 3.6 Document safe transform workflow in `BUILDING_AGENTS.md`

## 4. Natural language filter translation

- [x] 4.1 Create `iterable/ai/filter.py` with `translate_filter(expression, schema=None, **kwargs)`
- [x] 4.2 Define filter AST model and whitelist validator
- [x] 4.3 Bridge AST to `ops.filter` execution
- [x] 4.4 Reject expressions referencing SQL keywords or multi-statement input
- [x] 4.5 Add `tests/test_ai_filter.py` with allowed and rejected cases
- [x] 4.6 Add ops-filter spec delta for AI-assisted filter scenario

## 5. Prompt templates and caching

- [x] 5.1 Create `iterable/ai/prompts/` directory with versioned templates for doc, plan, suggest, filter
- [x] 5.2 Load templates via `importlib.resources`
- [x] 5.3 Add opt-in `cache=True` to `doc.generate()` with LRU cache keyed by content hash + params
- [x] 5.4 Add `cache_clear()` utility for tests
- [x] 5.5 Document caching behavior and privacy implications

## 6. Integration tests and markers

- [x] 6.1 Add `@pytest.mark.integration` tests for live OpenAI/Anthropic/Gemini (skip without env)
- [x] 6.2 Add VCR-style recorded fixtures in `tests/fixtures/ai_responses/` for optional replay
- [x] 6.3 Document running integration tests in `AGENTS.md` AI section
- [x] 6.4 CI: integration tests excluded by default, separate workflow job `ai-integration`

## 7. Privacy defaults

- [x] 7.1 Default `doc.generate()` cloud path to use `redact_for_llm` on samples when `pii_detect` unavailable (heuristic redaction on)
- [x] 7.2 Add `send_raw_samples=False` default for new AI functions
- [x] 7.3 Update integration guides with native provider examples using redaction

## 8. Tool surface updates (if Phase 3 merged)

- [x] 8.1 Add `tools.plan_conversion()` wrapper
- [x] 8.2 Add `tools.suggest_transform()` wrapper
- [x] 8.3 Add `tools.translate_filter()` wrapper
- [x] 8.4 Extend MCP server with plan/suggest tools (read-only)

## 9. Documentation and OpenSpec

- [x] 9.1 Expand `docs/docs/api/ai.md` with new functions
- [x] 9.2 Update `openspec/specs/ai/spec.md` Purpose if not done in Phase 1
- [x] 9.3 Add examples for each new capability

## 10. Verification

- [x] 10.1 `pytest tests/test_ai*.py -m "not integration" -v`
- [x] 10.2 `ruff check iterable tests && ruff format --check iterable tests`
- [x] 10.3 `openspec validate expand-ai-operations --strict`
