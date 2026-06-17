# Change: LLM-oriented format catalog and context utilities

## Why

Agents need machine-readable format knowledge to choose correct `open_iterable()` arguments,
optional extras, and conversion paths. The new `format_registry` centralizes structural metadata
but lacks human-oriented descriptions, examples, and limitations. `capabilities.py` exposes
runtime introspection but no stable export for grounding. Phase 2 of the LLM readiness roadmap
adds an `iterable.catalog` module, LLM-enriched descriptors, context-budgeting helpers, and CI
artifacts (`formats.json`) so agents answer "how do I read format X?" without reading source.

## What Changes

- **MODIFIED**: Extend `FormatDescriptor` with optional LLM fields: `description`, `example_args`,
  `limitations`, `doc_url`.
- **ADDED**: `iterable/catalog/` module with `list_formats()`, `describe_format(id)`,
  `export_catalog(format=...)`, merging registry + capabilities.
- **ADDED**: `iterable.ai.context` (or `iterable.helpers.llm_context`) with `sample_for_llm()`
  and `redact_for_llm()` for safe prompt construction.
- **ADDED**: `dev/formats.json` CI artifact (or `docs/static/formats.json`) from catalog export.
- **ADDED**: Script to generate Docusaurus format doc stubs for undocumented formats from registry.
- **ADDED**: Cursor skill `.cursor/skills/ai-integration/SKILL.md`.
- **ADDED**: Tests for catalog API and context utilities.

Backward compatible: new descriptor fields default to empty/None; existing derivation unchanged.

## Impact

- Affected specs: `format-registry` (new, from `add-format-metadata-registry`), `llm-catalog` (new)
- Affected code: `iterable/helpers/format_registry.py`, new `iterable/catalog/`,
  `iterable/ai/context.py`, `dev/scripts/`, `.cursor/skills/ai-integration/`, CI workflow
- Depends on: `add-format-metadata-registry` (merged or complete)
- Blocks: `add-agent-tool-surfaces` (tools will call catalog)
