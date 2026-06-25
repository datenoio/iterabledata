---
name: ai-integration
description: AI and LLM integration for IterableData. Use when working with iterable.ai, autodoc, LLM providers, catalog, or agent-facing APIs.
---

# AI Integration

## Core APIs

```python
from iterable.ai import doc
from iterable.ai.context import sample_for_llm, redact_for_llm
from iterable.catalog import describe_format, export_catalog, list_formats
from iterable.ops import inspect
```

## Documentation generation

```python
# Local provider (no API key)
doc.generate("data.csv", provider="lmstudio", base_url="http://localhost:1234/v1")

# With inspect
inspect.analyze("data.csv", autodoc=True, autodoc_provider="openai")
```

Install: `pip install iterabledata[ai]` or `pip install -e ".[ai]"`.

## Block-based documentation (`generate_blocks`)

```python
from iterable.ai import doc

result = doc.generate_blocks(
    "data.csv",
    blocks=["general", "schema", "quality", "examples", "statistics"],  # codebook also available
    context={"title": "Population", "territory": "Russia"},
    progress=lambda e: print(e.stage.value, e.progress),
)
result["blocks"]["schema"]["data"]["fields"]   # structured data per block
result["full_document_markdown"]               # assembled document
```

- Each block returns `{markdown, data}`; `statistics` is computed (no LLM); `lineage`/`geo_coverage` are deferred stubs.
- LLM blocks use structured output (`provider.generate_structured`) with Pydantic models in `iterable.ai.models`.
- Sampling adapts to file size (`MAX_ROWS_SAMPLING`); stats support `null_fraction`, `top_values`, `is_dictionary` (`DICT_THRESHOLD`).
- Provider config via `LLM_PROVIDER`/`LLM_BASE_URL`/`LLM_API_KEY`/`LLM_DEFAULT_MODEL`; `provider="openai-compatible"` targets any OpenAI-compatible endpoint.
- `doc.generate(..., blocks=[...])` delegates to `generate_blocks`; without `blocks` the legacy single-document path is unchanged.

## Safe LLM sampling

Always sample and redact before cloud APIs:

```python
rows = sample_for_llm("data.csv", max_rows=10, strategy="stratified")
safe = redact_for_llm(rows)
```

## Format catalog for agents

```python
describe_format("xml")  # includes example_args, limitations, capabilities
export_catalog(format="json")  # full catalog; committed at dev/formats.json
```

## Testing

- Mock providers: `patch("iterable.ai.doc.get_provider")`
- Mark AI tests: `@pytest.mark.ai`
- Never commit API keys; use env vars (`OPENAI_API_KEY`, etc.)

## Specs

- `openspec/specs/ai/spec.md`
- `openspec/changes/LLM_READINESS_ROADMAP.md`

## Constraints

- Do not use `exec()` on LLM-generated code; use `pipeline()` with explicit functions.
- No CLI in this repo; expose via Python API only.
