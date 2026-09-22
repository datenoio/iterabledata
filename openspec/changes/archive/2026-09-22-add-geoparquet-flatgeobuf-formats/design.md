## Context

GeoParquet is Parquet plus standardized geospatial metadata and geometry encodings. FlatGeobuf is a feature container with streaming layout and an optional packed spatial index. Existing geospatial readers generally expose GeoJSON-like features.

## Goals / Non-Goals

- Goals:
  - Reuse Parquet/Arrow implementation and batches for GeoParquet.
  - Preserve geospatial metadata on round trip.
  - Stream FlatGeobuf features and exploit its index when requested.
  - Maintain one consistent feature row model.
- Non-Goals:
  - Implement a general GIS engine or reprojection library.
  - Automatically transform CRS.
  - Duplicate the complete Parquet reader.

## Decisions

### GeoParquet profile

`geoparquet` is a profile backed by `ParquetIterable`. On read, Parquet footer metadata is inspected for the GeoParquet `geo` metadata key. Explicit `format="geoparquet"` is supported; automatic `.parquet` opening selects the profile when valid metadata is present without a full data scan.

### Feature mapping

Default rows are GeoJSON-like Features with `geometry` and `properties`. An advanced `geometry_mode="wkb"` preserves raw geometry bytes for batch/zero-copy workflows. Geometry column, primary geometry, CRS, encoding, geometry types, and bounding-box metadata remain available.

### GeoParquet writes

Writers accept feature rows or raw WKB mode, encode geometry according to declared options, and write valid GeoParquet metadata. Unknown metadata fields are preserved when safely possible.

### FlatGeobuf

FlatGeobuf yields the same feature shape. Sequential reading is bounded; `bbox` uses the packed index when present. Lack of an index falls back only when explicitly allowed and is reported in diagnostics.

## Risks / Trade-offs

- Geometry conversion can dominate batch performance. Mitigation: raw WKB mode and batch adapters.
- GeoParquet specification versions evolve. Mitigation: preserve version metadata and test supported versions.
- Python FlatGeobuf backends may vary in streaming/index support. Mitigation: pin a supported range and capability-test it.

## Migration Plan

Implement GeoParquet read/profile detection first, then write metadata preservation, followed by FlatGeobuf sequential read/write and indexed selection. Both begin experimental until golden interoperability fixtures pass.

## Open Questions

- Which GeoParquet version/geometry encodings are mandatory for the first stable release?
- Should automatic GeoParquet profile detection change the class id returned for all metadata-bearing `.parquet` files?
