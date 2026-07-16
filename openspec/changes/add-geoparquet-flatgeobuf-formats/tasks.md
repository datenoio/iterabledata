## 1. Shared geospatial model

- [x] 1.1 Define feature/WKB row mappings and metadata preservation rules.
- [x] 1.2 Add optional dependency extras and complete descriptors for GeoParquet and FlatGeobuf.
- [ ] 1.3 Add geometry/CRS helper tests independent of file backends.

## 2. GeoParquet

- [x] 2.1 Detect valid GeoParquet metadata from the Parquet footer and support explicit profile selection.
- [ ] 2.2 Implement feature and raw-WKB reads with geometry column, CRS, encoding, type, and bbox metadata.
- [x] 2.3 Implement valid metadata-aware writes and round-trip preservation.
- [x] 2.4 Reuse Parquet batch/projection paths without duplicating the base reader.

## 3. FlatGeobuf

- [ ] 3.1 Add extension and magic-byte detection plus clear missing-dependency errors.
- [x] 3.2 Implement bounded sequential feature reading and `read_bulk()`.
- [x] 3.3 Implement bbox selection using the spatial index and documented fallback behavior.
- [ ] 3.4 Implement bounded writes and round trips.

## 4. Tests and documentation

- [ ] 4.1 Add official/interoperable golden fixtures with multiple geometry types and CRS metadata.
- [ ] 4.2 Add malformed, truncated, missing-index, empty, optional-dependency, and memory tests.
- [ ] 4.3 Add GeoParquet metadata and FlatGeobuf index performance benchmarks.
- [x] 4.4 Document format profiles, row modes, metadata, selection, limitations, and examples.
- [ ] 4.5 Run geospatial/columnar representative CI and strict OpenSpec validation.
