## Context

`DeltaIterable`, `IcebergIterable`, and `HudiIterable` currently support read-only access and explicitly raise `WriteNotSupportedError`. Their descriptors mark `writable=False`. Native Python clients already expose write APIs (`deltalake.write_deltalake` / table merges, PyIceberg append/overwrite, Hudi writers depending on package).

## Goals / Non-Goals

- Goals:
  - Enable `mode='w'` (and documented append/overwrite) for all three formats where backends allow.
  - Keep peak write memory bounded by `batch_size` where the backend supports incremental commits/flushes.
  - Update capability metadata so tools/`is_writable` reflect reality.
- Non-Goals:
  - Full merge/upsert/CDC feature parity with Spark writers in v1 (may phase upserts).
  - Catalog provisioning UX beyond what read paths already require.
  - Changing Lance/Vortex/Paimon write behavior.

## Decisions

### Per-format v1 write scope

| Format | v1 write modes | Notes |
|--------|----------------|-------|
| Delta | create / overwrite / append | Prefer `deltalake` writer APIs; schema evolution opt-in later |
| Iceberg | append (and create if catalog APIs allow) | Require existing catalog+table coords like reads; overwrite if safe |
| Hudi | append/copy-on-write subset | Pin supported `hudi`/`pyhudi` API; defer MOR-heavy upserts if unstable |

### Shared write contract

- Buffer dict rows → Arrow table/batches → backend write at `batch_size` or on `close()`.
- Infer schema from first batch or accept explicit schema in `iterableargs`.
- Fail fast on schema incompatibility rather than silently coercing destructive changes.
- Declare `write_memory="bounded"` only when flushes are incremental; otherwise `"whole_output"` or `"backend_defined"`.

### Descriptor updates

Set `writable=True` only after tests pass for that format. Maturity may remain `partial`/`experimental` until upserts and cloud catalogs are covered.

## Risks / Trade-offs

- **Backend API differences** → Thin adapters per format; shared tests for round-trip only.
- **Hudi Python maturity** → May ship Delta+Iceberg writes first with Hudi behind a feature flag or later task if the client cannot append reliably.
- **Catalog credentials** → Reuse read-path catalog configuration; no new secret-handling inventiveness.

## Migration Plan

1. Delta append/overwrite + descriptor flip + tests.
2. Iceberg append (+ create if feasible) + tests.
3. Hudi writable subset or documented deferral with tasks updated.
4. Docs and capability export updates.

## Open Questions

- Should Iceberg overwrite be in v1 or append-only?
- Is the current `hudi` extra package sufficient for writes, or is a different client required?
