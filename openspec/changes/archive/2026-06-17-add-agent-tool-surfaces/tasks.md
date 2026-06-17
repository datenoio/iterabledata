## 1. iterable.tools core wrappers

- [x] 1.1 Create `iterable/tools/__init__.py` with uniform `ToolResult` dict helper
- [x] 1.2 Implement `detect_format(path)` wrapping `detect_file_type()`
- [x] 1.3 Implement `describe_capabilities(format_id)` using `catalog.describe_format()`
- [x] 1.4 Implement `read_sample(path, n=10, redact=False)` using `open_iterable` + `sample_for_llm`/`redact_for_llm`
- [x] 1.5 Implement `infer_schema(path, **kwargs)` wrapping `ops.schema.infer()`
- [x] 1.6 Implement `analyze_dataset(path, autodoc=False, **kwargs)` wrapping `ops.inspect.analyze()`
- [x] 1.7 Implement `compute_stats(path, **kwargs)` wrapping `ops.stats.compute()`
- [x] 1.8 Implement `convert_file(input_path, output_path, confirm=False, dry_run=False)` wrapping `convert()`
- [x] 1.9 Implement `generate_documentation(path, **kwargs)` wrapping `ai.doc.generate()`
- [x] 1.10 Implement `validate_data(path, rules, **kwargs)` wrapping `validate` module
- [x] 1.11 Add `tests/test_tools.py` for all wrappers (mocked I/O where needed)

## 2. Tool JSON schemas

- [x] 2.1 Create `iterable/tools/schemas.py` with OpenAI function definitions for all tools
- [x] 2.2 Add Anthropic tool schema export `to_anthropic_tools()`
- [x] 2.3 Add JSON Schema export `to_json_schema()` for generic agents
- [x] 2.4 Commit schema snapshots in `tests/fixtures/tool_schemas/`
- [x] 2.5 Add snapshot tests detecting accidental schema breakage

## 3. LangChain bundle (optional extra)

- [x] 3.1 Add `langchain` optional extra to `pyproject.toml` (`langchain-core`)
- [x] 3.2 Create `iterable/tools/langchain.py` with `get_tools()` returning `Tool` instances
- [x] 3.3 Add example `examples/ai/langchain_agent.py`
- [x] 3.4 Document LangChain setup in docs hub page

## 4. Pydantic models for AI JSON output

- [x] 4.1 Create `iterable/ai/models.py` with `DocumentationResult`, `FieldMetadata`, etc.
- [x] 4.2 Add `validate_output: bool` parameter to `doc.generate()`
- [x] 4.3 Validate JSON output against models when enabled; log warnings on mismatch
- [x] 4.4 Add tests with fixture JSON payloads

## 5. MCP server (optional extra)

- [x] 5.1 Add `mcp` optional extra to `pyproject.toml`
- [x] 5.2 Create `iterable/mcp/server.py` registering core tools (read-first set)
- [x] 5.3 Expose stdio entry point `iterable-mcp` via `[project.scripts]`
- [x] 5.4 Implement tools: detect_format, read_sample, infer_schema, analyze_dataset, generate_documentation
- [x] 5.5 Defer convert_file write to phase with `confirm=True` gate
- [x] 5.6 Add `docs/docs/integrations/MCP.md` setup guide (Cursor, Claude Desktop)
- [x] 5.7 Add `tests/test_mcp_server.py` with mocked MCP protocol

## 6. Documentation hub

- [x] 6.1 Create `docs/docs/integrations/BUILDING_AGENTS.md` canonical hub
- [x] 6.2 Consolidate cross-links from CLAUDE.md, OPENAI.md, GEMINI.md, AI_FRAMEWORKS.md
- [x] 6.3 Add `docs/docs/api/tools.md` API reference
- [x] 6.4 Update `llms.txt` with tools and MCP sections

## 7. Examples

- [x] 7.1 Add `examples/ai/openai_function_calling.py`
- [x] 7.2 Add `examples/ai/anthropic_tools.py`
- [x] 7.3 Update `examples/ai/README.md`

## 8. Verification

- [x] 8.1 `pytest tests/test_tools.py tests/test_mcp_server.py -v`
- [x] 8.2 `ruff check iterable tests && ruff format --check iterable tests`
- [x] 8.3 `openspec validate add-agent-tool-surfaces --strict`
