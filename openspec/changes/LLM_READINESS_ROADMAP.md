# LLM Readiness Roadmap (OpenSpec) — archived 2026-06-17

All four phases below were implemented and archived under `openspec/changes/archive/2026-06-17-*`.

| Phase | Change ID | Focus | Spec capabilities |
|-------|-----------|-------|-------------------|
| 1 | [fix-ai-llm-foundation](./fix-ai-llm-foundation/proposal.md) | Trust, autodoc, llms.txt, docs site, safe guides | `ops-inspect`, `ai`, `llm-discoverability` |
| 2 | [add-llm-catalog](./add-llm-catalog/proposal.md) | Format catalog, LLM context utils, formats.json | `format-registry`, `llm-catalog` |
| 3 | [add-agent-tool-surfaces](./add-agent-tool-surfaces/proposal.md) | iterable.tools, schemas, LangChain, MCP | `agent-tools`, `ai` |
| 4 | [expand-ai-operations](./expand-ai-operations/proposal.md) | Providers, planning, transforms, NL filters | `ai`, `ops-filter` |

## Dependency graph

```
fix-ai-llm-foundation
        │
        ▼
add-llm-catalog ──────────────────┐
        │                         │
        ▼                         ▼
add-agent-tool-surfaces    expand-ai-operations
        │                         │
        └───────────┬─────────────┘
                    ▼
           (tool wrappers for new AI ops — Phase 4 §8)
```

## Related work

- [add-format-metadata-registry](./add-format-metadata-registry/proposal.md) — prerequisite for Phase 2 catalog (complete in tree)
- Archived: [enhance-ai-documentation](../archive/2026-01-30-enhance-ai-documentation/proposal.md) — prior `doc.generate()` scope

## Validation

```bash
openspec validate fix-ai-llm-foundation --strict
openspec validate add-llm-catalog --strict
openspec validate add-agent-tool-surfaces --strict
openspec validate expand-ai-operations --strict
```

## Approval gate

Do not implement until each change proposal is reviewed and approved per `openspec/AGENTS.md`.
