#!/usr/bin/env python3
"""Generate root llms.txt for LLM/agent discoverability."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "llms.txt"

CONTENT = """# IterableData (iterabledata)

> Unified Python library for streaming read/write across 100+ data formats.

## Entry points

- `from iterable.helpers.detect import open_iterable` — open any supported file (auto-detect format/compression)
- `from iterable.convert import convert` — convert between formats
- `from iterable.ops import inspect, schema, stats, transform, filter` — high-level data operations
- `from iterable.ai import doc` — AI-powered dataset documentation (`doc.generate()`)
- `from iterable import validate, ingest` — validation and database ingestion

## Optional extras

- `[ai]` — LLM documentation (`openai`, `requests`); providers: openai, openrouter, ollama, lmstudio, perplexity
- `[db]` — database read engines and ingest backends
- `[dev]` — pytest, ruff, mypy, pre-commit

Install: `pip install iterabledata[ai]` or `pip install -e ".[dev]"` from source.

## Examples

- `examples/ai/generate_documentation.py` — AI documentation generation
- `examples/convert/` — format conversion
- `examples/pipeline/` — streaming pipelines
- `tests/test_*.py` — usage patterns per format

## Agent / contributor docs

- `AGENTS.md` — setup, conventions, testing for coding agents
- `openspec/AGENTS.md` — OpenSpec proposal workflow
- `CONTRIBUTING.md` — human contributor onboarding
- `.cursor/skills/` — Cursor skills (format-implementation, testing-patterns, openspec-workflows)

## Specifications

- `openspec/specs/` — capability specs (including `ai`, `ops-inspect`, `convert`)
- `openspec/changes/LLM_READINESS_ROADMAP.md` — phased LLM readiness plan

## API documentation

- Published: https://datenoio.github.io/iterabledata/
- Source: `docs/docs/api/` (ai.md, open-iterable.md, convert.md)
- Integrations: `docs/integrations/` (AI_FRAMEWORKS.md, CLAUDE.md, OPENAI.md, GEMINI.md)

## Conventions

- Always use `with open_iterable(path) as source:` context managers
- No CLI in this repo (library only); use Python API
- New features with behavior changes require OpenSpec proposals under `openspec/changes/`
"""


def main() -> None:
    OUTPUT.write_text(CONTENT, encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
