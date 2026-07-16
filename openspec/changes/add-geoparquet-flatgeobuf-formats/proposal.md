# Change: Add GeoParquet and FlatGeobuf Support

## Why

IterableData supports many geospatial formats but lacks the two most natural high-throughput additions: the GeoParquet metadata profile for existing Parquet/Arrow data and FlatGeobuf for indexed streaming features. Both should reuse existing feature semantics and columnar/batch infrastructure rather than becoming isolated readers.

## What Changes

- Add a metadata-aware `geoparquet` profile over the Parquet implementation.
- Detect GeoParquet from file metadata, preserve CRS/geometry/bounding-box metadata, and support raw WKB or GeoJSON-like feature rows.
- Add streaming FlatGeobuf read/write support with magic detection and optional bounding-box index queries.
- Add optional geospatial dependency metadata, golden fixtures, round trips, malformed-input behavior, and bounded-memory tests.

## Dependencies

- Coordinate descriptors/capabilities with `unify-format-capability-metadata`.
- Reuse batch transfer and projection pushdown from `add-native-batch-conversion` when available.

## Impact

- Affected specs: `geospatial-formats`
- Affected code: Parquet profile/metadata handling, new FlatGeobuf datatype, detection/registry, geospatial helpers, docs/tests
- New dependencies: optional maintained geometry/FlatGeobuf libraries in a geospatial extra
