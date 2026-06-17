## Context

Documentation-only AI underuses the ops layer. Undatum-style `doc` is done; next value is
helping agents plan ETL without generating arbitrary code.

## Goals / Non-Goals

- Goals:
  - Provider parity with integration guides.
  - Declarative outputs only for transforms and conversion plans.
  - Safe execution path for NL filters via existing `ops.filter`.
- Non-Goals:
  - Arbitrary code generation or `exec()`.
  - Full natural-language ETL without human review.
  - Embedding/RAG store (future work).

## Decisions

- Decision: `suggest_transform()` returns JSON spec:
  `{ "operations": [{"op": "rename", "from": "...", "to": "..."}, ...] }` applied by a new
  `apply_transform_spec()` in `ops.transform` (or existing transform ops).
- Decision: `plan_conversion()` uses `catalog.describe_format()` for source/target capabilities;
  output includes recommended `open_iterable` kwargs, codec notes, and warnings.
- Decision: `translate_filter()` produces AST nodes whitelisted to field comparisons, AND/OR, IN,
  regex (bounded); rejects raw SQL strings.
- Decision: Anthropic uses `anthropic` SDK; Gemini uses `google-genai`; Azure uses `openai` with
  `azure_endpoint`.
- Decision: Caching is opt-in `cache=True` on `doc.generate()`, in-memory LRU default, pluggable backend later.

## Risks / Trade-offs

- NL filter misinterpretation → always return parseable AST + human-readable explanation; never auto-apply without explicit call.
- Provider API drift → integration tests optional, mocked by default.
- Transform spec scope creep → start with rename, fill, replace, select, filter ops only.

## Open Questions

- Whether `apply_transform_spec()` belongs in this change or a follow-up `add-transform-spec-executor`.
