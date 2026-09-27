## 1. Hermetic tests

- [x] 1.1 Move every fixture-mutating write/round-trip test to `tmp_path` or a copied fixture.
- [x] 1.2 Add a post-test `git diff --exit-code -- tests/fixtures` CI assertion.
- [x] 1.3 Add `.hypothesis` to the effective pytest recursion exclusions without replacing useful defaults.
- [x] 1.4 Add a minimal-install import and CSV/JSONL smoke job.
- [x] 1.5 Add a Python 3.13 leg to the cross-platform CI test matrix.

## 2. Representative optional coverage

- [x] 2.1 Define columnar, scientific, geospatial, bio, database, lakehouse, and codec extra families.
- [x] 2.2 Add Linux CI jobs for each representative family with explicit skip/failure reporting.
- [x] 2.3 Publish per-family and core coverage reports.
- [x] 2.4 Introduce reviewed staged coverage floors and document how they increase.
- [x] 2.5 Print the explicit base-env vs full-dev-env coverage picture and COVERAGE FLOOR CHECK lines in CI.

## 3. Typing and static quality

- [x] 3.1 Fix the three errors in the current core Mypy CI command.
- [x] 3.2 Centralize local/CI Mypy targets and record package-scoped historical baselines.
- [x] 3.3 Enforce no new typing errors in changed files and expand zero-error blocking packages incrementally.
- [x] 3.4 Clear actionable Pydocstyle and Vulture findings, then enable reviewed blocking thresholds.
- [x] 3.5 Refactor the seven E/F complexity hotspots with focused behavior tests.
- [x] 3.6 Add an advisory Radon `--min D` complexity gate to CI; flip to blocking once 3.5 lands.

## 4. Documentation and repository status

- [x] 4.1 Replace all format-page template placeholders with verified examples, install extras, capabilities, memory behavior, and limitations.
- [x] 4.2 Refresh or retire stale improvement/unfinished-proposal status documents.
- [x] 4.3 Add or update contributor guidance for OpenSpec triggers, fixture immutability, minimal/family test commands, and artifact checks.
- [x] 4.4 Archive completed OpenSpec changes through the standard archive workflow before merging overlapping deltas.

## 5. Verification

- [x] 5.1 Run core checks and representative family jobs from clean environments.
- [x] 5.2 Confirm the test run leaves the worktree clean.
- [x] 5.3 Confirm blocking type/static/coverage gates are green and documented.
