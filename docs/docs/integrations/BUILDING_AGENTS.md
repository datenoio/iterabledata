# Building AI Agents with IterableData

Canonical guide for integrating IterableData with LLM agents, IDEs, and automation.

## Quick start

```python
from iterable.tools import detect_format, read_sample, infer_schema

# Uniform JSON envelopes
fmt = detect_format("data.csv")
rows = read_sample("data.csv", n=10, redact=True)
sch = infer_schema("data.csv")
```

Install extras as needed:

```bash
pip install iterabledata[ai]        # documentation generation
pip install iterabledata[langchain] # LangChain StructuredTools
pip install iterabledata[mcp]       # MCP server (iterable-mcp)
```

## Layers

1. **`iterable.tools`** — stable tool functions with `ok` / `data` / `error` envelopes
2. **`iterable.tools.schemas`** — OpenAI, Anthropic, and JSON Schema exports
3. **`iterable.catalog`** — format metadata for routing (`describe_format("xml")`)
4. **`iterable.ai.context`** — `sample_for_llm`, `redact_for_llm` before cloud APIs
5. **`iterable-mcp`** — stdio MCP server for Cursor / Claude Desktop

## OpenAI function calling

```python
from iterable.tools import schemas

functions = schemas.to_openai_functions()
# Pass to client.chat.completions.create(..., tools=functions)
result = schemas.call_tool("read_sample", {"path": "data.csv", "n": 5})
```

See [examples/ai/openai_function_calling.py](https://github.com/datenoio/iterabledata/blob/main/examples/ai/openai_function_calling.py).

## Anthropic tools

```python
tools = schemas.to_anthropic_tools()
result = schemas.call_tool("infer_schema", {"path": "data.csv"})
```

See [examples/ai/anthropic_tools.py](https://github.com/datenoio/iterabledata/blob/main/examples/ai/anthropic_tools.py).

## LangChain

```python
from iterable.tools.langchain import get_tools
```

## MCP (Cursor, Claude Desktop)

Configure MCP to run `iterable-mcp` after `pip install iterabledata[mcp]`.
See [MCP.md](MCP.md).

## Safety

- Use `read_sample` + `redact_for_llm` before sending data to cloud LLMs
- `convert_file` requires `confirm=True` to write files
- Do not `exec()` LLM-generated code; use explicit `pipeline()` transforms

## Further reading

- [API: Agent Tools](../api/tools.md)
- [API: Catalog](../api/catalog.md)
- [API: AI](../api/ai.md)
- [AI Frameworks](frameworks.md) · [OpenAI](https://github.com/datenoio/iterabledata/blob/main/docs/integrations/OPENAI.md) · [Claude](https://github.com/datenoio/iterabledata/blob/main/docs/integrations/CLAUDE.md) · [Gemini](https://github.com/datenoio/iterabledata/blob/main/docs/integrations/GEMINI.md)
- [llms.txt](https://github.com/datenoio/iterabledata/blob/main/llms.txt) — machine index
