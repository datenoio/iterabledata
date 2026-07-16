## 1. Hermetic tests

- [x] 1.1 Move every fixture-mutating write/round-trip test to `tmp_path` or a copied fixture.
- [x] 1.2 Add a post-test `git diff --exit-code -- tests/fixtures` CI assertion.
- [x] 1.3 Add `.hypothesis` to the effective pytest recursion exclusions without replacing useful defaults.
- [x] 1.4 Add a minimal-install import and CSV/JSONL smoke job.

## 2. Representative optional coverage

- [x] 2.1 Define columnar, scientific, geospatial, bio, database, lakehouse, and codec extra families.
- [x] 2.2 Add Linux CI jobs for each representative family with explicit skip/failure reporting.
- [ ] 2.3 Publish per-family and core coverage reports.
- [ ] 2.4 Introduce reviewed staged coverage floors and document how they increase.

## 3. Typing and static quality

- [ ] 3.1 Fix the three errors in the current core Mypy CI command.
- [ ] 3.2 Centralize local/CI Mypy targets and record package-scoped historical baselines.
- [ ] 3.3 Enforce no new typing errors in changed files and expand zero-error blocking packages incrementally.
- [ ] 3.4 Clear actionable Pydocstyle and Vulture findings, then enable reviewed blocking thresholds.
- [ ] 3.5 Refactor the seven E/F complexity hotspots with focused behavior tests.

## 4. Documentation and repository status

- [ ] 4.1 Replace all format-page template placeholders with verified examples, install extras, capabilities, memory behavior, and limitations.
- [ ] 4.2 Refresh or retire stale improvement/unfinished-proposal status documents.
- [x] 4.3 Add or update contributor guidance for OpenSpec triggers, fixture immutability, minimal/family test commands, and artifact checks.
- [ ] 4.4 Archive completed OpenSpec changes through the standard archive workflow before merging overlapping deltas.

## 5. Verification

- [ ] 5.1 Run core checks and representative family jobs from clean environments.
- [ ] 5.2 Confirm the test run leaves the worktree clean.
- [ ] 5.3 Confirm blocking type/static/coverage gates are green and documented.
