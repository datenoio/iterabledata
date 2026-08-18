## 1. Canonical public API in user-facing copy

- [x] 1.1 Document the five canonical imports (`open_iterable`, `convert`, `ops`, `catalog`, `tools`) in `llms.txt` and getting-started
- [x] 1.2 Rewrite getting-started pages (installation, quick-start, basic-usage, best-practices) to use `from iterable import open_iterable`, `with` statements, and `from iterable.convert import convert`
- [x] 1.3 Update README quick start, `AGENTS.md`, format-page template, and iterabledata-development skill to the public import
- [x] 1.4 Mechanically replace user-facing `from iterable.helpers.detect import open_iterable` / `convert.core` / `pipeline.core` in `docs/`, `examples/`, and integration guides (split mixed detect imports)

## 2. Machine indexes

- [x] 2.1 Update `dev/scripts/generate_llms_txt.py` to emit canonical imports, install-vs-import naming, tools/MCP, catalog, and skill links
- [x] 2.2 Add `llms-full.txt` generator content with prompt-shaped recipes (read, write, convert, XML tagname, inspect, extras)
- [x] 2.3 Copy `llms.txt` and `llms-full.txt` into `docs/static/` from the generator
- [x] 2.4 Regenerate committed `llms.txt` / `llms-full.txt` at repo root

## 3. Portable skill, cookbook, and positioning

- [x] 3.1 Add portable usage skill at `skills/iterabledata/SKILL.md`
- [x] 3.2 Add `examples/cookbook/` runnable scripts plus README (read, convert, inspect) using canonical imports
- [x] 3.3 Add docs pages: cookbook and when-to-use (vs pandas/stdlib), and register them in `docs/sidebars.js`
- [x] 3.4 Clarify `pyproject.toml` description/keywords (PyPI name vs import name; streaming ETL / format conversion)

## 4. Tests and agent onboarding

- [x] 4.1 Extend `tests/test_llms_txt.py` for `llms-full.txt` sections, canonical imports, and docs/static copies
- [x] 4.2 Add docs-consistency tests that fail if listed user-facing paths teach the internal `open_iterable` import or `convert.core` as the default
- [x] 4.3 Add a cookbook smoke test against `tests/fixtures/2cols6rows.csv`
- [x] 4.4 Update `openspec/changes/LLM_READINESS_ROADMAP.md` with this phase
- [x] 4.5 Run `openspec validate improve-llm-code-generation --strict`, ruff, and targeted pytest

## 5. Docs site discoverability

- [x] 5.1 Link `llms.txt` from the docs navbar and footer
- [x] 5.2 Add a homepage CTA and sidebar category for coding agents (cookbook, skill docs, MCP)
