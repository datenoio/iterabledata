# Change: Agent tool surfaces — iterable.tools, schemas, and optional MCP server

## Why

Integration guides show copy-paste LangChain/Claude wrappers, but IterableData lacks a versioned,
JSON-serializable tool layer. Every agent integrator reimplements the same operations. Phase 3
exposes stable tool functions, OpenAI/Anthropic-compatible schemas, an optional LangChain bundle,
Pydantic-validated AI JSON output, and an optional MCP server extra so Cursor, Claude Desktop,
and custom agents can use IterableData without custom glue code.

## What Changes

- **ADDED**: `iterable/tools/` package with thin wrappers returning JSON-serializable dicts:
  `detect_format`, `describe_capabilities`, `read_sample`, `infer_schema`, `analyze_dataset`,
  `compute_stats`, `convert_file`, `generate_documentation`, `validate_data`.
- **ADDED**: `iterable.tools.schemas` exporting OpenAI function and Anthropic tool JSON schemas.
- **ADDED**: Optional `iterable.tools.langchain` module (`get_tools()` list).
- **ADDED**: Optional MCP server under `iterable/mcp/` or separate package path, extra
  `iterabledata[mcp]` in `pyproject.toml`.
- **ADDED**: Pydantic models for `ai.doc.generate(format="json")` response validation.
- **ADDED**: Documentation: "Building AI Agents with IterableData" hub page; MCP setup guide.
- **ADDED**: Tests for tool wrappers (no live LLM) and schema snapshot tests.

No changes to core `open_iterable()` API. MCP is optional dependency only.

## Impact

- Affected specs: `agent-tools` (new), `ai` (structured output)
- Affected code: new `iterable/tools/`, `iterable/mcp/`, `iterable/ai/models.py`, `pyproject.toml`,
  `docs/docs/api/`, `examples/ai/`
- Depends on: `fix-ai-llm-foundation`, `add-llm-catalog` (catalog used by describe_capabilities)
- Blocks: none (Phase 4 can proceed in parallel for provider expansion)
