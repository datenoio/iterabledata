## Context

108 formats with scattered docs (26 without pages) force agents to guess `iterableargs` (e.g.
XML `tagname`). The format registry is the right SSOT; this change adds an LLM-facing export layer.

## Goals / Non-Goals

- Goals:
  - Single `describe_format("xml")` call returns everything an agent needs.
  - Version-controlled `formats.json` for CI drift detection.
  - Utilities to sample/redact data before external LLM calls.
- Non-Goals:
  - MCP server or LangChain tools (Phase 3).
  - Auto-writing prose descriptions via LLM (manual/curated descriptions first).

## Decisions

- Decision: `FormatDescriptor` gains optional `description: str | None`, `example_args: dict | None`,
  `limitations: tuple[str, ...]`, `doc_url: str | None`. Seeded incrementally; empty defaults OK.
- Decision: `export_catalog()` returns JSON-serializable dict; `include_capabilities=True` merges
  `get_format_capabilities()` per format (best-effort on import errors).
- Decision: `sample_for_llm(iterable, max_rows=..., max_tokens=..., strategy="head"|"stratified")`
  estimates token budget via character heuristic (documented, not tokenizer-exact).
- Decision: `redact_for_llm()` applies column-name heuristics + optional Metacrafter PII fields;
  composes with `sample_for_llm()`.
- Decision: CI job writes `dev/formats.json`; test fails if export differs from committed file when
  registry changes.

## Risks / Trade-offs

- Curating 108 descriptions is labor-intensive → seed top 30 formats first; stub others from id/module.
- Capability merge at export time can be slow → cache per-format in export script only.

## Open Questions

- Publish `formats.json` on docs site vs keep in `dev/` only.
