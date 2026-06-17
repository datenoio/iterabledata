## Context

IterableData ships `iterable.ai.doc.generate()` and documents `inspect.analyze(autodoc=True)`,
but the inspect integration was left as `pass` after the AI module landed. External agents
discover the library via README, PyPI, and (when working) GitHub Pages — all currently
misaligned for LLM grounding.

## Goals / Non-Goals

- Goals:
  - Zero silent failures on documented AI integration paths.
  - Published docs reachable at a single canonical URL.
  - `llms.txt` as a stable, version-controlled agent index.
  - Integration guides safe for copy-paste by coding agents.
- Non-Goals:
  - New AI capabilities beyond wiring autodoc (see `expand-ai-operations`).
  - MCP or tool schemas (see `add-agent-tool-surfaces`).
  - Format catalog export (see `add-llm-catalog`).

## Decisions

- Decision: `inspect.analyze(autodoc=True)` calls `ai.doc.generate()` with `format="json"`,
  `include_schema=False` (schema already computed), and merges `documentation` /
  `documentation_meta` into the analyze result. On missing `[ai]` extra, raise `ImportError`
  with install instructions (do not swallow).
- Decision: `llms.txt` lives at repo root and is regenerated in CI only when a manual
  `dev/scripts/generate_llms_txt.py` is run (script committed; CI check optional in this phase).
- Decision: Docs site URL follows the actual GitHub org/repo (`datenoio/iterabledata`) unless
  a custom domain is configured; README and `pyproject.toml` URLs updated to match.
- Decision: Integration guide security pass replaces `exec(transform_code)` examples with
  `pipeline(process_func=...)` using hand-written or library-validated transform dicts.

## Risks / Trade-offs

- `autodoc=True` adds latency and optional API cost → document in `analyze()` docstring;
  default remains `False`.
- `llms.txt` can drift → add a lightweight test asserting required sections exist.

## Open Questions

- Custom domain for docs (e.g. `docs.iterabledata.io`) vs GitHub Pages default URL.
