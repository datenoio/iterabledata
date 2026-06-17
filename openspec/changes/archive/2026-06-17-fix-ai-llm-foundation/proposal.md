# Change: AI/LLM foundation — trust, spec alignment, and discoverability

## Why

The AI/LLM readiness audit identified critical gaps between documented behavior and
implementation: `inspect.analyze(autodoc=True)` is a no-op stub despite OpenSpec and user-guide
promises; the `ai` and `ops-inspect` specs still have placeholder Purpose sections; integration
guides recommend unsafe patterns (`exec()` on LLM-generated code); and the docs site is
unreachable (404), blocking LLM crawlers and external agents from grounding on published
documentation.

Phase 1 of the LLM readiness roadmap must restore trust before adding new agent surfaces.

## What Changes

- **MODIFIED**: Wire `inspect.analyze(autodoc=True)` to `iterable.ai.doc.generate()` with
  structured result keys (`documentation`, `documentation_meta`) and clear errors when AI extras
  are missing.
- **MODIFIED**: Fill in Purpose sections for `openspec/specs/ai/spec.md` and
  `openspec/specs/ops-inspect/spec.md`.
- **ADDED**: Root-level `llms.txt` machine index (entry points, extras, examples, spec links).
- **ADDED**: `CONTRIBUTING.md` linking `AGENTS.md`, OpenSpec, and Cursor skills for human and AI
  contributors.
- **MODIFIED**: Harden `docs/integrations/*.md` — remove `exec()` patterns; recommend declarative
  transforms via `pipeline()`; document data residency and redaction expectations.
- **MODIFIED**: Fix GitHub Pages docs deployment (org/repo URL mismatch) so
  `docs/docusaurus.config.js` and `deploy-docs.yml` publish to a working URL.
- **ADDED**: AI spec conformance tests mapping OpenSpec scenarios to mocked/integration tests.
- **ADDED**: README "AI Quick Start" section (5–10 lines, local-provider-first).

No breaking API changes. `autodoc=False` behavior is unchanged.

## Impact

- Affected specs: `ops-inspect`, `ai`, `llm-discoverability` (new)
- Affected code: `iterable/ops/inspect.py`, `tests/test_inspect.py`, `tests/test_ai.py`,
  `docs/docusaurus.config.js`, `.github/workflows/deploy-docs.yml`, `docs/integrations/*`,
  `README.md`, `llms.txt`, `CONTRIBUTING.md`
- Depends on: none (first phase of LLM roadmap)
- Blocks: `add-llm-catalog`, `add-agent-tool-surfaces`, `expand-ai-operations`
