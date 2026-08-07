## Why

Dataset documentation is useful for humans, but AI agents still lack a portable,
file-scoped instruction pack that tells them how to load, query, and safely use a
specific dataset. A new optional documentation block can generate a neutral
agent-skill document from the same profile evidence already used for other blocks.

## What Changes

- Add an optional LLM-backed documentation block `agent_skill`.
- Add a Pydantic model and JSON Schema for the structured skill payload.
- Add `generate_agent_skill()` and register it in `BLOCK_REGISTRY`.
- Keep the block **out of** `DEFAULT_BLOCKS` so library callers opt in explicitly.
- Generate skill text in the request/job language already threaded through `BlockContext`.
- Produce a neutral agent-skill format (YAML frontmatter + Markdown body), not a
  Cursor-only private format, while remaining usable by Cursor-compatible agents.
- Do **not** change existing block contracts or make `agent_skill` required.

## Capabilities

### New Capabilities

- none

### Modified Capabilities

- `ai`: extend block-based documentation with an optional `agent_skill` block,
  structured output model, and registry entry.

## Impact

- Affected code: `iterable/ai/models.py`, `iterable/ai/blocks.py`, tests under
  `tests/test_ai_blocks.py`, possibly docs/examples.
- Downstream: `dateno-datadoc` will consume the new block via its iterabledata
  adapter once this library change is available.
- Non-goals: service job runtime, web UI, artifact downloads, zip bundles,
  `reference.md`, portal integrations, making the block part of default generation.
