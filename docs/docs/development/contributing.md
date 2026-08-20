# Contributing

Thank you for contributing. IterableData supports both human developers and AI coding agents.

## Getting started

```bash
git clone https://github.com/datenoio/iterabledata.git
cd iterabledata
pip install -e ".[dev]"
pre-commit install
pytest --verbose
```

See the repository [AGENTS.md](https://github.com/datenoio/iterabledata/blob/main/AGENTS.md) for setup, code style, testing, and project structure. Pre-commit hooks mirror CI lint and format checks (`ruff`).

## Spec-driven changes

Behavior changes and new capabilities need an OpenSpec proposal before implementation:

1. Read [openspec/AGENTS.md](https://github.com/datenoio/iterabledata/blob/main/openspec/AGENTS.md)
2. List active changes: `openspec list`
3. Scaffold `openspec/changes/<change-id>/` with `proposal.md`, `tasks.md`, and spec deltas
4. Validate: `openspec validate <change-id> --strict`
5. Implement only after the proposal is approved

## Pull requests

- Tests pass: `pytest --verbose`
- Lint and format: `ruff check iterable tests && ruff format --check iterable tests`
- Include tests for new behavior
- Update these docs when changing public APIs
- This package is a **library only** — do not add a CLI or `[project.scripts]` entry point

## Adding a format or codec

See [Adding formats](adding-formats.md).

## Quality and release

Committed files under `tests/fixtures/` are read-only inputs. Write tests to `tmp_path`. Before a release, see [Releasing](releasing.md).

## Related

- [Type stubs](type-stubs.md)
- [Plugin system](/api/plugins) — third-party formats, codecs, and drivers without changing core
- [License](/license)
