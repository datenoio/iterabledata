# Change: Add Zarr v2/v3 Format Support

## Why

Zarr is the largest scientific-array gap beside HDF5 and NetCDF and is designed for chunked local and cloud storage. Supporting it extends IterableData's bounded-memory array workflows, but requires an explicit array-to-row mapping rather than treating a multidimensional store as an ordinary table.

## What Changes

- Add experimental Zarr v2/v3 detection and an optional `zarr` dependency extra.
- Expose groups/arrays through `list_tables()` and select an array explicitly when a store is ambiguous.
- Iterate dense, structured, and record-like arrays by a configurable leading axis/chunk with a documented row mapping.
- Push array/slice/chunk selection into the Zarr backend before Python conversion.
- Support bounded writes/appends for compatible arrays and local/fsspec-backed stores.

## Dependencies

- Coordinate descriptor fields with `unify-format-capability-metadata`.
- Reuse the selection/native-batch model from `add-native-batch-conversion` when available; row iteration remains independently usable.

## Impact

- Affected specs: `zarr-format`
- Affected code: new datatype, format descriptor/detection, optional dependencies, tests, fixtures, docs
- New dependency: optional maintained `zarr` package and its supported store dependencies
