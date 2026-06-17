---
sidebar_position: 17
title: Agent Tools
description: JSON-serializable tool wrappers for LLM agents
---

# Agent Tools

The `iterable.tools` module exposes stable, JSON-serializable wrappers for common
IterableData operations. All tools return `{"ok": true, "data": ...}` or
`{"ok": false, "error": "...", "code": "..."}`.

## Tools

| Tool | Description |
|------|-------------|
| `detect_format(path)` | Detect format and compression |
| `describe_capabilities(format_id)` | Format metadata + capabilities |
| `read_sample(path, n=10, redact=False)` | Bounded row sample |
| `infer_schema(path)` | Schema inference |
| `analyze_dataset(path, autodoc=False)` | Structure analysis |
| `compute_stats(path)` | Column statistics |
| `convert_file(input, output, confirm=False, dry_run=False)` | Format conversion |
| `generate_documentation(path, **kwargs)` | AI documentation |
| `validate_data(path, rules, mode="stats")` | Row validation |

```python
from iterable.tools import detect_format, read_sample, infer_schema

result = detect_format("data.csv")
if result["ok"]:
    print(result["data"]["format"])

sample = read_sample("data.csv", n=5, redact=True)
schema = infer_schema("data.csv")
```

## Schema export

```python
from iterable.tools import schemas

openai_tools = schemas.to_openai_functions()
anthropic_tools = schemas.to_anthropic_tools()
schemas.call_tool("detect_format", {"path": "data.csv"})
```

## LangChain

```bash
pip install iterabledata[langchain]
```

```python
from iterable.tools.langchain import get_tools

tools = get_tools()  # list of StructuredTool instances
```

## MCP server

```bash
pip install iterabledata[mcp]
iterable-mcp
```

See [MCP integration guide](../integrations/MCP.md).

## Related

- [Format catalog](catalog.md)
- [Building AI agents](../integrations/BUILDING_AGENTS.md)
- [AI documentation](ai.md)
