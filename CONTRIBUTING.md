# Contributing to IterableData

Thank you for contributing. This project supports both human developers and AI coding agents.

## Getting started

```bash
git clone https://github.com/datenoio/iterabledata.git
cd iterabledata
pip install -e ".[dev]"
pre-commit install
pytest --verbose
```

See **[AGENTS.md](AGENTS.md)** for full setup, code style, testing, and project structure. Pre-commit hooks mirror CI lint/format checks (ruff) and run optional quality scans locally.

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

- **[llms.txt](llms.txt)** — short machine-readable index of entry points
- **[llms-full.txt](llms-full.txt)** — copy-paste recipes for coding models
- **[skills/iterabledata/SKILL.md](skills/iterabledata/SKILL.md)** — portable usage skill for other repositories
- **[docs/integrations/](docs/integrations/)** — AI framework integration guides
- **API docs:** https://datenoio.github.io/iterabledata/
- **License:** code is MIT; documentation and data are [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## Quality and release checks

Committed files under `tests/fixtures/` are read-only inputs. Write tests to
`tmp_path`; the test harness also runs legacy round trips in a disposable copy
and CI fails if tracked fixtures change. For a minimal environment run
`pytest --no-cov`; representative optional families are exercised with
`.[parquet]`, `.[geospatial]`, `.[alignment,bio]`, and `.[compression]`.

Before a release, validate the exact artifacts with `python -m build`,
`python -m twine check dist/*`, `check-wheel-contents`, and
`python dev/scripts/verify_dist.py dist/*`. OpenSpec changes must be validated
strictly and their task checklists must reflect only completed work.

## Coverage floors (staged)

Coverage floors rise in reviewed stages; only Stage 1 is enforced today.

- **Stage 1 — global floor 50 (enforced).** `fail_under = 50` in
  `pyproject.toml` `[tool.coverage.report]` is enforced by pytest-cov on the
  full-dev-env CI matrix legs. The base-env leg and the per-family jobs pass
  `--cov-fail-under=0` because missing extras make their totals unrepresentative.
- **Stage 2 — per-family targets (advisory, not enforced).** The
  `optional-family-smoke` CI jobs run their tests under serial coverage, print a
  `term-missing` report scoped to the family modules, and upload coverage
  artifacts (`coverage-<family>`). Reference numbers measured locally with
  bounded serial runs (full dev extras installed):

  | family | tests | measured | advisory floor |
  | --- | --- | --- | --- |
  | text | `test_csv.py` + `test_jsonl.py` | 49.5% (csv 55.2%, jsonl 39.3%) | 45 |
  | columnar | `test_parquet.py` + `test_arrow.py` | 60.0% (parquet 54.0%, arrow 67.2%) | 55 |
  | codecs | `test_codec_profiles.py` | 34.3% | 30 |

  Remaining families (geospatial, bio, scientific, database, lakehouse) get
  their floors from the CI artifact reports before any enforcement.
- **Stage 3 — aspiration.** Raise the global floor toward 60 once the family
  floors hold in CI; bump `fail_under` only after a reviewed measurement.

Never combine `pytest -n auto` (xdist) with coverage: `tests/conftest.py`
chdirs to a disposable runtime root in `pytest_configure`, which scatters
per-worker coverage data. Coverage runs are always serial.

## Static analysis gates and ratchets

- **Mypy core gate (blocking).** `mypy --follow-imports=skip` over the core
  file list in `.github/workflows/ci.yml`; those modules also carry
  `disallow_untyped_defs` in `pyproject.toml`. Expand the list only with files
  verified zero-error under the *exact combined gate command* — checking files
  one at a time misses cross-module errors that appear when the core modules
  are analyzed together.
- **No new typing errors in changed files (advisory in CI).**
  `python dev/scripts/mypy_changed_files.py [BASE_REF]` diffs
  `iterable/*.py` against the base ref (default `origin/main`, fallback
  `main`) and fails if mypy reports errors in the changed files. In CI it is
  `continue-on-error: true` for now and needs full git history
  (`actions/checkout` with `fetch-depth: 0`, already set on the lint job).
- **Full-package mypy ratchet (advisory).** `python dev/scripts/mypy_ratchet.py`
  compares against `dev/mypy_baseline.txt`.
- **Pydocstyle ratchet (advisory in CI).** Baseline: **22 findings**
  (`pydocstyle iterable`, google convention) — counts must not exceed the
  baseline; the CI gate compares and is advisory until findings are cleared.
- **Vulture ratchet (advisory in CI).** Baseline: **17 findings**
  (`vulture iterable --min-confidence 80`) — same must-not-exceed rule.
