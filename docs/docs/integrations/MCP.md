# MCP Server for IterableData

Run IterableData operations as [Model Context Protocol](https://modelcontextprotocol.io/) tools in Cursor, Claude Desktop, and other MCP clients.

## Install

```bash
pip install iterabledata[mcp]
```

## Run (stdio)

```bash
iterable-mcp
```

The server registers read-first tools: `detect_format`, `describe_capabilities`, `read_sample`, `infer_schema`, `analyze_dataset`, `generate_documentation`, and gated `convert_file` (writes require `confirm=True`).

## Cursor configuration

Add to MCP settings (example):

```json
{
  "mcpServers": {
    "iterabledata": {
      "command": "iterable-mcp",
      "args": []
    }
  }
}
```

Use the full path to `iterable-mcp` if it is not on `PATH`.

## Claude Desktop

Add a server entry in Claude Desktop MCP config pointing to `iterable-mcp` with stdio transport (same as above).

## Programmatic use

```python
from iterable.mcp import create_mcp_server

mcp = create_mcp_server()
mcp.run()
```

## Security

- Prefer `read_sample` with `redact=True` for sensitive data
- `convert_file` will not write unless `confirm=True`
- `generate_documentation` may call external LLM APIs when used

## See also

- [Building AI Agents](BUILDING_AGENTS.md)
- [Agent Tools API](../api/tools.md)
