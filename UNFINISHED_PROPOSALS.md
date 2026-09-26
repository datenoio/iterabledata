# Unfinished OpenSpec Proposals

This document is a dated snapshot of OpenSpec proposals that are not yet complete. A proposal is considered unfinished if it has unchecked tasks in its `tasks.md` file.

**Last Updated**: 2026-09-26

> **Note**: This file is a point-in-time snapshot. `openspec list` is the live source of truth for active changes; `openspec list --specs` lists capability specs.

## Summary

- **Total Active Proposals**: 2
- **Archived since the last snapshot**: 8 proposals — 6 under `openspec/changes/archive/2026-09-22-*` (the format-hardening batch plus `add-codec-performance-profiles` and `optimize-format-io-hot-paths`) and 2 more in the 2026-09-21 batch (`unify-format-capability-metadata`, `add-native-batch-conversion`)
- **Validation**: `openspec validate --all --strict` passes (69 items, 0 failures)

---

## Active (Unfinished) Proposals

| Change ID | Tasks complete | Created |
|---|---|---|
| `strengthen-repository-quality-gates` | 18/23 | 7/16/2026 |
| `harden-release-artifacts` | 15/17 | 7/16/2026 |

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
- The remaining 2 active proposals are partially implemented; see their `tasks.md` files for open work

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

**Total archived**: 54 proposals across 12 batches (74 dated archive directories including pre-OpenSpec-tracked entries)
