# Change: Validation Hooks for Every Writable Format

## Why

Write-time validation hooks (`_apply_validation_hooks`) exist on roughly a
quarter of writable formats; the rest accept records silently (plan 2026-09
§6.4). Users get inconsistent data-quality guarantees depending on which
format they pick.

## What Changes

- Roll out `_apply_validation_hooks` to every writable format (mechanical,
  registry-driven: enumerate `writable=True` descriptors and wire the hook in
  `write()`/`write_bulk()` paths that lack it).
- A conformance test walks all writable formats and fails if a write path
  bypasses validation, so future formats cannot regress.
- Behavior stays compatible: hooks default to the existing no-op policy unless
  a validator is configured.

## Impact

- Affected specs: `validation-consistency` (extended).
- Affected code: writable `iterable/datatypes/*` classes lacking hooks, tests.
- No new dependencies.

## Non-goals

- Changing validation semantics or adding new validators; this is coverage
  rollout only.
