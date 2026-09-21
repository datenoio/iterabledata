## Context

Business exchange formats complement existing spreadsheet and SQLite support. EDI is message-oriented; MDB is multi-table relational; Lotus 123 is a legacy spreadsheet.

## Goals / Non-Goals

- Goals:
  - Stream EDI segments/transactions, Access table rows, and Lotus sheet rows as dict records.
  - List Access tables and select explicitly when ambiguous.
- Non-Goals:
  - Full EDI mapping repositories / HIPAA validator suites.
  - Access forms/macros/VBA.
  - Write support for all three in v1 (Access/Lotus may be read-only).

## Decisions

### EDI

Provide a pragmatic parser mode: yield segment dicts (`segment_id`, `elements`) and optional transaction grouping. Support common X12 and EDIFACT line conventions; declare unsupported dialects.

### Access MDB

Use a maintained optional reader. `list_tables()` returns user tables; require `table=` when multiple exist. Prefer read-only.

### Lotus 123

Read first sheet by default or selected sheet via args; yield header-aware row dicts when a header row is present.

## Risks / Trade-offs

- Access drivers can be platform-specific → document supported platforms; skip CI where unavailable.
- EDI variability is high → keep v1 subset explicit and fixture-driven.

## Migration Plan

Experimental until representative fixtures pass. No breaking API changes.

## Open Questions

- Include `.accdb` in the same format id as `.mdb`?
- Default EDI granularity: segment vs transaction envelope?
