# Unfinished OpenSpec Proposals

This document is a dated snapshot of OpenSpec proposals that are not yet complete. A proposal is considered unfinished if it has unchecked tasks in its `tasks.md` file.

**Last Updated**: 2026-10-28

> **Note**: This file is a point-in-time snapshot. `openspec list` is the live source of truth for active changes; `openspec list --specs` lists capability specs.

## Summary

- **Total Active Proposals**: 7 (six added 2026-10-28 from the undatum integration review, see `IMPROVEMENT_PLAN_2026-10.md`)
- **Archived since the last snapshot**: 6 proposals under `openspec/changes/archive/2026-09-27-*` (`strengthen-repository-quality-gates` plus the five September feature tracks)
- **Validation**: `openspec validate --all --strict` passes (72 items, 0 failures)

---

## Active (Unfinished) Proposals

| Change ID | Tasks complete | Created |
|---|---|---|
| `harden-release-artifacts` | 16/17 | 7/16/2026 |
| `fix-json-serialization-fidelity` | 9/9 (ready to archive) | 10/28/2026 |
| `fix-csv-dialect-and-codec-options` | 12/12 (ready to archive) | 10/28/2026 |
| `fix-convert-silent-row-loss` | 9/9 (ready to archive) | 10/28/2026 |
| `fix-package-import-hygiene` | 11/11 (ready to archive) | 10/28/2026 |
| `update-convert-api-parity` | 8/8 (ready to archive) | 10/28/2026 |
| `optimize-json-csv-parquet-hot-paths` | 0/20 | 10/28/2026 |

The one remaining task is a single owner-approved real release run; all local release-artifact verification (clean-checkout build, twine, check-wheel-contents, wheel smoke test) is complete.

---

## Archived 2026-09-27 (6 proposals)

All archived with their spec deltas applied (`openspec archive <id> --yes`):

- `strengthen-repository-quality-gates` → new spec: `repository-quality`; spec update: `test-suite`
- `add-office-format-writes` → new spec: `office-format-writes` (XLSX/ODS/XML writers)
- `add-genuine-async-iteration` → new spec: `async-iteration` (`aopen_iterable` with `asyncio.to_thread` offload)
- `add-db-ingest-parity` → spec update: `ingest` (ClickHouse/MSSQL backends, opt-in pooling)
- `add-validation-hooks-rollout` → spec update: `validation-consistency` (hooks on all writable formats)
- `add-reference-plugin` → new spec: `plugin-ecosystem` (reference plugin under `examples/plugins/`)

After this batch there are **71 capability specs** (`openspec list --specs`).

---

## Archived 2026-09-22 (6 proposals)

All archived with their spec deltas applied (`openspec archive <id> --yes`):

- `extend-bioinformatics-formats` → spec update: `bioinformatics-formats` (CRAM/BED/GFF3/GTF hardening)
- `add-otlp-format-profiles` → new spec: `otlp-profiles` (OTLP logs/metrics/traces/profiles)
- `add-geoparquet-flatgeobuf-formats` → new specs: `geoparquet-format`, `flatgeobuf-format`
- `add-zarr-format` → new spec: `zarr-format`
- `add-codec-performance-profiles` → spec update: `compression-codecs`
- `optimize-format-io-hot-paths` → spec update: `datatype-implementation`

After this batch there are **67 capability specs** (`openspec list --specs`).

---

## Archived 2026-09-21 (23 proposals)

All 23 completed changes were archived with their spec deltas applied (`openspec archive <id> --yes`); none required `--skip-specs`. Archived as `openspec/changes/archive/2026-09-21-<id>`:

- `update-format-dependency-metadata` → spec update: `format-registry`
- `update-datatype-error-policy` → new spec: `error-handling`
- `update-streaming-capability-truth` → spec update: `datatype-implementation`
- `add-business-exchange-formats` → new spec: `business-exchange-formats`
- `add-esri-mapinfo-formats` → spec update: `geospatial-formats`
- `add-fst-hdt-iati-formats` → new specs: `fst-format`, `iati-format`; update: `rdf-formats`
- `add-geophysical-formats` → new spec: `geophysical-formats`
- `add-gis-grid-lidar-formats` → spec update: `geospatial-formats`
- `add-scientific-structure-formats` → new spec: `scientific-structure-formats`
- `add-webdataset-format` → new spec: `webdataset-format`
- `add-lakehouse-write-support` → new specs: `delta-format`, `hudi-format`, `iceberg-format`
- `add-paimon-table-support` → new spec: `paimon-table-format`
- `add-ducklake-format` → new spec: `ducklake-format`
- `add-paimon-row-mosaic-formats` → new specs: `paimon-mosaic-format`, `paimon-row-format`
- `add-untrusted-input-hardening` → new spec: `input-security`; update: `ops-filter`
- `add-performance-regression-gate` → new spec: `performance-regression`
- `refactor-core-entry-points` → new spec: `open-iterable-structure`
- `add-genomic-vcf-format` → new spec: `genomic-vcf-format`
- `refactor-full-load-readers-to-streaming` → spec update: `datatype-implementation`
- `update-codec-streaming` → new spec: `compression-codecs`
- `add-tar-container-format` → new spec: `tar-container`
- `add-geojsonseq-format` → spec update: `geospatial-formats`
- `update-test-suite-resilience` → new spec: `test-suite`

After this batch there are **63 capability specs** (`openspec list --specs`).

---

## Notes

- Proposals are considered "finished" when all tasks in `tasks.md` are checked
- Finished proposals should be archived using `openspec archive <change-id> --yes` (add `--skip-specs` for tooling-only changes with no spec deltas)
- The remaining active proposal is partially implemented; see its `tasks.md` file for open work

---

## Historical Context

### Previously Archived Proposals

**First batch (2026-01-27):**
- `add-atomic-writes`, `add-html-arff-formats`, `add-vortex-format`, `add-dataframe-bridges`, `add-clickhouse-support`

**Second batch (2026-01-27):**
- `add-additional-formats`, `add-bulk-convert`, `add-cloud-storage-support`, `add-error-handling-controls`

**Third batch (2026-01-27):**
- `add-format-capabilities`, `add-type-hints`

**Fourth batch (2026-01-27):**
- `add-table-listing`, `add-pcap-support`, `add-database-engines`

**Fifth batch (2026-01-27):**
- `extend-table-listing`, `add-observability`, `enhance-duckdb-pushdown`

**Sixth batch (2026-01-27):**
- `add-high-level-operations`

**Seventh batch (2026-01-28):**
- `implement-architecture-improvements`

**Eighth batch (2026-01-28):**
- `add-bulk-convert`, `add-clickhouse-support`, `add-cloud-storage-support`, `add-database-engines`, `add-observability`, `enhance-duckdb-pushdown`

**Ninth batch (2026-01-31):**
- `add-kmz-gpx-formats` → `2026-01-31-add-kmz-gpx-formats` (KMZ and GPX geospatial format support)

**Tenth batch (2026-02-03):**
- `improve-datatypes-consistency` → `2026-02-03-improve-datatypes-consistency` (validation hooks in write/write_bulk, SQLite fetchmany, TopoJSON single Topology, tests)

**Eleventh batch (2026-09-21):**
- 23 proposals listed in the "Archived 2026-09-21" section above

**Twelfth batch (2026-09-22):**
- 6 proposals listed in the "Archived 2026-09-22" section above

**Thirteenth batch (2026-09-27):**
- 6 proposals listed in the "Archived 2026-09-27" section above

**Total archived**: 60 proposals across 13 batches (80 dated archive directories including pre-OpenSpec-tracked entries)
