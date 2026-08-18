## Context

IterableData already shipped LLM-readiness phases 1–4 (catalog, tools, MCP, root `llms.txt`).
Those surfaces help an agent that already chose the library. Coding models still default to
pandas because public examples use `from iterable.helpers.detect import open_iterable`, mix
manual `.close()` with `with`, and do not match typical user prompts ("convert XML to JSONL").

## Goals / Non-Goals

- Goals:
  - One canonical public import for `open_iterable`, `convert`, `pipeline`, `ops`, and tools
  - Prompt-shaped recipes models can copy without editing import paths
  - Machine indexes (`llms.txt`, `llms-full.txt`) hosted on GitHub Pages
  - A portable skill other repos can drop in
  - Tests that keep user-facing docs on the canonical API
- Non-Goals:
  - Changing runtime behavior of `open_iterable` / `convert`
  - Adding a CLI
  - Rewriting every format page's prose (import lines only)
  - Paid LLM evals in CI (heuristic docs checks only)
  - Forcing pandas users off DataFrame analytics

## Decisions

- Decision: Canonical import is `from iterable import open_iterable`, already re-exported.
  Internal `iterable.helpers.detect` remains for `detect_file_type` and library tests.
- Decision: Canonical convert import is `from iterable.convert import convert` (already
  re-exported from `iterable.convert.__init__`). Same for `from iterable.pipeline import pipeline`.
- Decision: Portable skill lives at `skills/iterabledata/SKILL.md` so it can be copied into
  other projects. Repo Cursor skills stay development-oriented; the development skill is updated
  so agents working *on this repo* still generate the public import in user-facing examples.
- Decision: Bulk-replace import lines in `docs/`, `examples/`, `README.md`, `AGENTS.md`, and
  integration guides. Leave `tests/` and `iterable/` on whatever import they use today unless a
  file is an example script.
- Decision: `llms-full.txt` is generated alongside `llms.txt` and copied to `docs/static/` so
  GitHub Pages serves `/iterabledata/llms.txt` and `/iterabledata/llms-full.txt`.
- Alternatives considered: Re-export everything from `iterable` (`convert`, `detect_file_type`).
  Rejected for this change — keep the five documented imports small and already-exported.

## Risks / Trade-offs

- Docs churn across many format pages → Mitigation: mechanical import rewrite plus a CI grep test
  on a defined allow/deny file set
- Mixed imports (`open_iterable, detect_file_type`) → split into public + detect-module lines
- Historical CHANGELOG / archived OpenSpec text kept as-is (not user-facing copy-paste)

## Migration Plan

Docs-only. Old imports continue to work. No runtime migration.

## Open Questions

- None for this change. A later change can add an optional live LLM generation eval.
