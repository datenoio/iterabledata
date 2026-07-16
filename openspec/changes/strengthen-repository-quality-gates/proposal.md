# Change: Strengthen Repository Quality Gates

## Why

The default suite passes, but tracked fixtures are mutated, optional formats are underrepresented in CI, the blocking core Mypy command is red, full-package typing debt is large despite `py.typed`, coverage is uneven, and documentation/status files contain stale or placeholder content. Passing checks do not yet guarantee a clean checkout or representative package quality.

## What Changes

- Make fixtures immutable and fail CI if tests leave tracked fixture changes.
- Add minimal, cross-platform core, and representative optional-dependency CI layers with per-package coverage reporting.
- Restore the blocking core Mypy gate, establish explicit package baselines, and ratchet typing coverage toward the public `py.typed` promise.
- Clear and then gate the actionable Pydocstyle/Vulture backlog; refactor the measured E/F complexity hotspots.
- Replace placeholder format docs and keep repository/OpenSpec status documents current.

## Dependencies

- Archive `update-test-suite-resilience` before implementation; this proposal extends its `test-suite` capability.
- Coordinate performance jobs with `optimize-format-io-hot-paths` to avoid duplicate CI workloads.

## Impact

- Affected specs: `test-suite`, `repository-quality`
- Affected files: tests/fixtures usage, pytest configuration, CI workflows, Mypy configuration, docs, status/governance files, selected complex modules
- Compatibility: no public runtime API change; contributor and CI requirements become stricter
