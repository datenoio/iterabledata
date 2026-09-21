# Change: Add GIS Grid, LiDAR, and CZML Formats

## Why

Beyond FileGDB/MIF, Dateno stats still surface high-value geospatial iterable gaps: Esri ASCII Grid (`ascii grid` / `.asc`), ArcInfo Interchange (`e00`), LAS LiDAR (`las`), BAG bathymetry (`bag`), and Cesium CZML (`.czml`). These appear in open geospatial catalogs and map cleanly to row streams (cells, points, packets, or document objects).

## What Changes

- Add read support for Esri ASCII Grid / `.asc` as cell or row-oriented records.
- Add read support for ArcInfo Interchange `.e00` feature/coverage exports where practical.
- Add read support for LAS point clouds (and document LAZ as codec-composed if supported).
- Add read support for BAG bathymetric products as iterable depth/sample records or listed arrays.
- Add read support for CZML JSON document packets as iterable records.
- Register formats, optional deps, fixtures, tests, and docs.

## Impact

- Affected specs: `geospatial-formats`
- Affected code: new datatypes, registry/detection, optional extras, docs/tests
- New dependencies: optional LiDAR/BAG/grid libraries under geospatial or scientific extras
