## Context

These formats extend IterableData's geospatial surface beyond vector feature files into grids, point clouds, bathymetry, and Cesium timedocument streams. They share the need for explicit row mappings because native structures are not always "one GIS feature per row."

## Goals / Non-Goals

- Goals:
  - Provide bounded iteration for ASCII Grid cells/rows, LAS points, BAG samples/tiles, E00 exported features, and CZML packets.
  - Document row schemas clearly for each format.
- Non-Goals:
  - Full coverage/topology editing for E00.
  - GPU rendering or Cesium runtime behavior for CZML.
  - Guaranteed write support for every format in v1 (read-first is acceptable).

## Decisions

### ASCII Grid / ASC

Default to one record per grid cell with `row`, `col`, `x`, `y`, `value` (nodata excluded or flagged). An optional `mode="row"` MAY yield one record per grid row for bulk analytics.

### LAS

Yield one record per point with at least `x`, `y`, `z` and common dimensions when present (intensity, classification, return number). LAZ SHOULD compose with an existing codec or backend decompression rather than a separate format id when possible.

### BAG / E00 / CZML

- BAG: expose listed elevation/uncertainty arrays or sample points via `list_tables()` when multiple datasets exist.
- E00: best-effort feature extraction for common ARC/INFO interchange exports; unsupported coverage constructs fail clearly.
- CZML: iterate top-level packet objects as dict records (JSON streaming).

## Risks / Trade-offs

- Dense ASCII grids can be huge → streaming by row/cell is mandatory; warn on whole-array APIs.
- LAS backends differ on CRS/VLR handling → preserve metadata accessors, don't invent CRS transforms.
- E00 is underspecified in the wild → mark experimental and fixture-driven.

## Migration Plan

Introduce as experimental formats. Prefer read-only first; enable writes only where round-trip fixtures exist.

## Open Questions

- Should `.asc` auto-disambiguate from generic ASCII text via header sniffing (`NCOLS`/`NROWS`)?
- Is LAZ a codec alias or a distinct format profile?
