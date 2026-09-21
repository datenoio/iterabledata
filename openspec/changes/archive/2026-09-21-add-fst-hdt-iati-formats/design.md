## Context

`fst` is an R columnar on-disk frame format. HDT is a binary RDF compression format. IATI is an XML standard for aid activities. These are independent formats bundled because they are the remaining high-confidence niche gaps from the same stats review.

## Goals / Non-Goals

- Goals:
  - Stream fst rows, HDT triples, and IATI activities as dict records.
  - Keep HDT record shape compatible with existing RDF iterables where practical.
- Non-Goals:
  - Full IATI organisation/file-level validation suites.
  - HDT index construction toolkit beyond reading.
  - Write support for all three in v1.

## Decisions

### fst

Read-only row iteration with column subsetting when the backend allows. Missing dependency raises install guidance for an R/fst-capable extra or pure-Python reader if used.

### HDT

Yield triples as `{subject, predicate, object}` (and graph when available). Prefer a maintained HDT binding; otherwise document experimental status.

### IATI

Parse activity-oriented IATI XML; default yield one record per `iati-activity` with core fields flattened/nested as documented. Use existing XML extra patterns (`lxml`) when possible.

## Risks / Trade-offs

- fst Python ecosystem may be thin → may need rpy2 or an alternate reader; decide in implementation and keep experimental.
- Large IATI files need streaming XML → avoid full DOM loads.

## Migration Plan

Ship experimental. No breaking changes to existing RDF formats.

## Open Questions

- Is a pure-Python fst reader acceptable if feature-incomplete?
- IATI default grain: activity vs transaction?
