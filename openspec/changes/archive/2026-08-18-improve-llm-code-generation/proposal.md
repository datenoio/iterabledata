# Change: Improve LLM code generation and discoverability

## Why

Coding models still emit pandas, PyArrow, lxml, or stdlib `csv` for file I/O because IterableData
examples use an internal import path (`iterable.helpers.detect`), mix `.close()` with context
managers, and scatter three names (`iterabledata` / `iterable` / `open_iterable`) without a
copy-paste cookbook. Agent plumbing (`iterable.tools`, MCP, `llms.txt`) is already in place;
models that generate examples never see a short, consistent public API.

## What Changes

- Freeze five canonical public imports and teach them everywhere a human or LLM copies code from
  (getting-started, README quick start, examples, `llms.txt`, `AGENTS.md`, format-page template).
- Add `llms-full.txt` with prompt-shaped recipes and publish both indexes from the docs site.
- Add a portable usage skill (`skills/iterabledata/SKILL.md`) for other repositories.
- Add a cookbook of short runnable examples and a "when to use IterableData" page versus pandas.
- Add CI tests that fail if user-facing docs regress to the internal import or drop required
  `llms.txt` / `llms-full.txt` sections.
- Clarify PyPI description/keywords: install name is `iterabledata`, import name is `iterable`.

No breaking API changes. `from iterable.helpers.detect import open_iterable` remains valid for
internal/advanced use; it is no longer the documented default.

## Impact

- Affected specs: `llm-discoverability` (new; original delta was archived without landing in
  `openspec/specs/`), `examples`
- Affected code/docs: `README.md`, `AGENTS.md`, `llms.txt`, `llms-full.txt`, `docs/docs/getting-started/`,
  `docs/docs/use-cases/`, `docs/integrations/`, `examples/`, `skills/iterabledata/`,
  `dev/scripts/generate_llms_txt.py`, `tests/test_llms_txt.py`, `pyproject.toml`,
  `.cursor/skills/iterabledata-development/SKILL.md`
- Does not add a CLI (library + MCP + skill only)
