# Change: Reference Plugin Package

## Why

The plugin loader, registry, and author docs exist, but no published reference
plugin proves the ecosystem story end-to-end (plan 2026-09 §6.5). A real
installable example validates the packaging metadata, discovery mechanism, and
documentation all at once.

## What Changes

- Create a minimal example plugin (e.g. a `.journal`-style newline-delimited
  log format or an uppercase-transform codec) in `examples/plugins/` with full
  packaging metadata (entry points, pyproject).
- Tests install it into a throwaway venv and verify discovery + use through
  `open_iterable()`.
- Docs: the plugin author guide references the example as the canonical
  starting point.

## Impact

- Affected specs: new `plugin-ecosystem` capability.
- Affected code: `examples/plugins/` (new), tests, docs. No core library
  changes expected — a goal is proving the loader suffices as-is.

## Non-goals

- Publishing to PyPI from this repo's CI (the example documents the process;
  actual publication is an owner decision).
