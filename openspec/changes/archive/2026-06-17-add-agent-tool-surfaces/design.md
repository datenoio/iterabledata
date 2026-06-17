## Context

Agents need stable tool names and JSON responses. IterableData ops already exist but return
Python objects unsuitable for direct LLM tool results. MCP is the emerging standard for IDE agents.

## Goals / Non-Goals

- Goals:
  - Eight core tools with stable names and versioned schemas.
  - MCP server exposing read/inspect/convert/doc operations.
  - Validated JSON from `ai.doc.generate(format="json")`.
- Non-Goals:
  - Replacing LangChain/CrewAI — only provide official bundles.
  - CLI in this repo (library + MCP only per AGENTS.md scope).
  - Write-capable MCP tools without explicit confirmation (read-first MVP).

## Decisions

- Decision: Tool functions live in `iterable.tools` and always return `dict[str, Any]` with
  `ok: bool`, `data` or `error` keys for uniform agent handling.
- Decision: `convert_file` MCP/tool wrapper requires explicit `output_path`; dry-run mode returns
  planned conversion without writing.
- Decision: MCP server implemented with `mcp` Python SDK (optional extra); stdio transport first.
- Decision: Pydantic models in `iterable.ai.models` validate JSON doc output; validation optional
  via `validate_output=True` on `doc.generate()`.
- Decision: LangChain integration is a thin adapter in `iterable.tools.langchain`, extra
  `iterabledata[langchain]` depends on `langchain-core`.

## Risks / Trade-offs

- MCP SDK churn → pin minimum version in optional extra.
- Tool surface area increases maintenance → schemas tested via snapshot files.
- `convert_file` over MCP is destructive → require `confirm=True` parameter for writes.

## Open Questions

- Ship MCP as subpackage vs separate PyPI distribution (start subpackage).
- HTTP MCP transport (defer to follow-up).
