# LLM Readiness Roadmap (OpenSpec)

Phases 1–4 were implemented and archived under `openspec/changes/archive/2026-06-17-*`.
Phase 5 (`improve-llm-code-generation`) made coding models *choose* IterableData by freezing
canonical public imports, recipes, and a portable usage skill.
Phase 6 (`distribute-agent-discovery`) puts those indexes on MCP / skill / llms.txt
surfaces crawlers and IDEs actually retrieve.

| Phase | Change ID | Focus | Spec capabilities |
|-------|-----------|-------|-------------------|
| 1 | [fix-ai-llm-foundation](./archive/2026-06-17-fix-ai-llm-foundation/proposal.md) | Trust, autodoc, llms.txt, docs site, safe guides | `ops-inspect`, `ai`, `llm-discoverability` |
| 2 | [add-llm-catalog](./archive/2026-06-17-add-llm-catalog/proposal.md) | Format catalog, LLM context utils, formats.json | `format-registry`, `llm-catalog` |
| 3 | [add-agent-tool-surfaces](./archive/2026-06-17-add-agent-tool-surfaces/proposal.md) | iterable.tools, schemas, LangChain, MCP | `agent-tools`, `ai` |
| 4 | [expand-ai-operations](./archive/2026-06-17-expand-ai-operations/proposal.md) | Providers, planning, transforms, NL filters | `ai`, `ops-filter` |
| 5 | [improve-llm-code-generation](./archive/2026-08-18-improve-llm-code-generation/proposal.md) | Canonical imports, llms-full.txt, usage skill, cookbook | `llm-discoverability`, `examples` |
| 6 | [distribute-agent-discovery](./archive/2026-08-18-distribute-agent-discovery/proposal.md) | MCP `server.json`, well-known llms.txt, prompt-eval, directory guide | `llm-discoverability`, `examples`, `agent-tools` |

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
        improve-llm-code-generation
                    │
                    ▼
        distribute-agent-discovery
```

## Related work

- [add-format-metadata-registry](./archive/2026-06-17-add-format-metadata-registry/proposal.md) — prerequisite for Phase 2 catalog
- Archived: [enhance-ai-documentation](./archive/2026-01-30-enhance-ai-documentation/proposal.md) — prior `doc.generate()` scope

## Validation

```bash
openspec validate --specs --strict
```
