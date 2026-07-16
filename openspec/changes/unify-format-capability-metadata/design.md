## Context

The current descriptor type is a useful center, but values are duplicated in `_READONLY_MEMBERS`, `_TEXT_TYPE_ORDER`, `_FLAT_TYPE_ORDER`, dependency maps, LLM metadata, magic signatures, and capability heuristics. Method existence also makes inherited base loops look like optimized bulk support.

## Goals / Non-Goals

- Goals:
  - Provide one reviewable metadata record per canonical format.
  - Generate legacy structures and catalog/docs views deterministically.
  - Represent unknown and backend-dependent behavior honestly.
  - Distinguish API availability from native performance characteristics.
- Non-Goals:
  - Dynamically benchmark formats during capability queries.
  - Import every optional dependency to build the catalog.
  - Remove backward-compatible registry constants.

## Decisions

### Descriptor fields

Descriptors will include canonical identity/aliases, module/class, text/flat/write flags, install extra, magic signatures, maturity, read/write memory class, API and native bulk support, totals/tables, codec composition, projection/filter/slice support, and path/stream/cloud constraints. LLM/docs fields remain on the same record.

### Tri-state and enumerated values

Boolean capabilities use `True`, `False`, or `None`. Memory uses `bounded`, `whole_input`/`whole_output`, `backend_defined`, or `unknown`. Maturity uses `stable`, `experimental`, or `partial`. Unknown is preferable to optimistic inference.

### Generated compatibility structures

`DATATYPE_REGISTRY`, read-only/text/flat collections, dependency hints, magic matching, catalog export, and docs matrices will be derived from descriptors. Ordering remains explicit on descriptors or the canonical descriptor sequence.

### Conformance, not source inspection

Tests may inspect method ownership and instantiate formats with available dependencies to check declarations, but runtime capability queries return descriptor values. Inherited base `read_bulk()` means API bulk is available; native bulk is true only when declared and conformance-tested.

### Versioned catalog

Catalog output will contain a schema version. Adding backward-compatible fields increments the minor version; incompatible shape/semantic changes increment the major version.

## Risks / Trade-offs

- Populating 111 descriptors is laborious. Mitigation: generate an audit table from current registries and require explicit review of unknowns.
- Declarations can drift. Mitigation: conformance tests and docs/catalog full-object comparison.
- Catalog additions may affect strict consumers. Mitigation: schema version and documented compatibility policy.

## Migration Plan

1. Extend descriptor/schema types with backward-compatible defaults.
2. Generate and review a completeness report.
3. Populate every built-in descriptor.
4. Switch consumers one at a time to derived data.
5. Remove redundant private tables after equivalence tests pass.

## Open Questions

- Should codec composition be a simple tri-state or a list of supported codec/source combinations?
- Should projection/filter/slice be individual fields or a structured `selection` object?
