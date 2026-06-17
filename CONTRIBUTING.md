# Contributing to IterableData

Thank you for contributing. This project supports both human developers and AI coding agents.

## Getting started

```bash
git clone https://github.com/datenoio/iterabledata.git
cd iterabledata
pip install -e ".[dev]"
pytest --verbose
```

See **[AGENTS.md](AGENTS.md)** for full setup, code style, testing, and project structure.

## Spec-driven changes

Behavior changes and new capabilities require an OpenSpec proposal before implementation:

1. Read **[openspec/AGENTS.md](openspec/AGENTS.md)** for the workflow.
2. List active changes: `openspec list`
3. Scaffold under `openspec/changes/<change-id>/` with `proposal.md`, `tasks.md`, and spec deltas.
4. Validate: `openspec validate <change-id> --strict`
5. Implement only after proposal approval; mark tasks complete in `tasks.md`.

## Cursor skills

AI assistants in Cursor can use project skills in **`.cursor/skills/`**:

- `iterabledata-development` — core conventions
- `format-implementation` — adding formats
- `testing-patterns` — test conventions
- `openspec-workflows` — proposals and specs
- `database-engine-implementation` — DB engines

## Pull requests

- All tests pass: `pytest --verbose`
- Lint and format: `ruff check iterable tests && ruff format --check iterable tests`
- Include tests for new behavior
- Update docs when changing public APIs
- Describe changes clearly in the PR

## LLM / agent consumers

- **[llms.txt](llms.txt)** — machine-readable index of entry points and docs
- **[docs/integrations/](docs/integrations/)** — AI framework integration guides
- **API docs:** https://datenoio.github.io/iterabledata/
