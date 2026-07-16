## Context

The review observed a green test suite that rewrote seven tracked fixtures, 329 environment-dependent skips, three errors in the nominally blocking Mypy command, 1,224 full-package Mypy errors, uneven branch coverage, and small but persistent documentation/static-analysis backlogs.

## Goals / Non-Goals

- Goals:
  - Make a green build imply a clean checkout and representative feature coverage.
  - Restore truthful blocking type checks and reduce debt incrementally.
  - Give optional dependency failures clear ownership by family.
  - Keep docs and status artifacts usable rather than placeholder-heavy.
- Non-Goals:
  - Install the entire `all` extra in every matrix leg.
  - Fix all historical Mypy errors in one change.
  - Raise coverage through assertion-light tests.

## Decisions

### Layered CI matrix

CI will have a minimal import/core smoke job, a supported cross-platform `[dev]` core matrix, and Linux representative-extra jobs grouped by format family. Live services/providers remain scheduled or manually dispatched.

### Immutable fixtures

Committed fixtures are read-only inputs. Write and round-trip tests use `tmp_path` copies or generated output. CI runs a post-test fixture diff check.

### Typing ratchet

The existing core check becomes green immediately. Additional packages receive recorded error budgets/floors, and changed files may not add errors. Packages move into the blocking set as their baseline reaches zero.

### Risk-weighted coverage

Core and family jobs publish separate coverage. Floors increase in stages and prioritize failure cleanup, transactions, resource handling, and round trips.

### Static/documentation gates

Actionable Pydocstyle/Vulture findings are cleared before gating. Complexity is reduced in the seven measured E/F functions through staged refactors with behavior tests. Format pages must not retain template markers.

## Risks / Trade-offs

- More CI jobs increase cost and runtime. Mitigation: family grouping, dependency caches, and non-duplicative matrices.
- Typing ratchets can block unrelated work. Mitigation: package-scoped baselines and changed-file policy.
- Post-test diffs can be platform-sensitive for generated files. Mitigation: never generate into tracked fixture paths.

## Migration Plan

1. Repair fixture writes and the three core Mypy failures.
2. Add clean-tree and minimal-install checks.
3. Add representative-extra jobs and coverage reports.
4. Establish typing/static-analysis ratchets.
5. Refactor complexity hotspots and finish docs/status cleanup.

## Open Questions

- Which optional format families should be blocking on every PR versus nightly?
- What initial package-specific coverage floors best match current installed extras?
