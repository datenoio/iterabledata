## Context

See `proposal.md` for motivation. iterabledata already has a block registry,
per-block Pydantic models, and structured LLM generation used by
`generate_blocks()`. Downstream services such as dateno-datadoc opt into blocks
by name; blocks omitted from `DEFAULT_BLOCKS` remain library-optional.

## Goals / Non-Goals

**Goals:**
- Add a first-class optional `agent_skill` block with structured output.
- Generate a neutral agent-skill Markdown document with YAML frontmatter.
- Keep deterministic dataset facts (format, fields, display name) injectable from
  `BlockContext` rather than invented by the model.
- Use the existing block language/`BlockContext.language` for skill text.

**Non-Goals:**
- Shipping the block in `DEFAULT_BLOCKS`.
- Cursor-only packaging, zip bundles, or `reference.md`.
- Service-side job artifacts, downloads, or UI.
- Making lineage/geo blocks concrete in this change.

## Decisions

1. **Block id = `agent_skill`**
   - Rationale: stable snake_case like existing blocks; clear product meaning.
   - Alternative considered: `skill` (too generic), `cursor_skill` (too vendor-specific).

2. **Structured payload + rendered skill markdown**
   - Rationale: keep machine-checkable fields (`name`, `description`, when-to-use,
     safety, dataset caveats, workflow steps) while emitting the portable document
     body agents load as the block `markdown`.
   - Alternative considered: only a markdown string (harder to validate and merge
     deterministic facts).

3. **Neutral skill format**
   - Minimal frontmatter: `name`, `description`.
   - Body sections: when to use, dataset facts, workflow, safety constraints,
     example analysis steps tied to real fields.
   - Alternative considered: Cursor directory layout with scripts/ (deferred).

4. **Not in `DEFAULT_BLOCKS`**
   - Callers must pass `blocks=[..., "agent_skill"]` or equivalent.
   - Matches “always optional” product decision and avoids unexpected LLM cost.

5. **Language follows `BlockContext.language`**
   - No separate skill-language parameter in the library API for MVP.

6. **Evidence inputs**
   - Prompt uses schema, samples, stats, and file metadata already on
     `BlockContext`; no new profiling APIs.

## Risks / Trade-offs

- [Model invents columns] → Keep field names in prompt from schema; consumers may
  reject unknown fields.
- [Skill encourages unsafe actions] → Prompt and schema include read-only /
  no-network constraints; consumers add stronger gates.
- [Large datasets overflow prompts] → Reuse existing schema/sample truncation
  helpers already used by other blocks.
- [Format drift across agents] → Keep frontmatter minimal and document the
  neutral contract; vendor-specific packaging can wrap later.

## Migration Plan

1. Land model + generator + registry behind explicit block selection.
2. Release iterabledata version consumed by dateno-datadoc.
3. No migration for existing callers: behavior unchanged unless they request the
   new block.
