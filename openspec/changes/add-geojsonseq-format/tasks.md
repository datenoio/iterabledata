## 1. Implementation

- [x] 1.1 Create `iterable/datatypes/geojsonseq.py` with `GeoJSONSeqIterable(BaseFileIterable)` reading one Feature per line
- [x] 1.2 Handle the optional RFC 8142 record separator (`\x1e`) prefix on each line
- [x] 1.3 Implement `write()`/`write_bulk()` emitting one Feature object per line
- [x] 1.4 Declare `is_streaming()` True

## 2. Registry and detection

- [x] 2.1 Add `geojsonseq` descriptor with extensions `.geojsonl`, `.geojsons`
- [x] 2.2 Add content detection: JSON object per line with `"type": "Feature"`

## 3. Tests and docs

- [x] 3.1 Add fixtures (`tests/fixtures/2cols6rows.geojsonl` equivalent with features)
- [x] 3.2 Read, write, and round-trip tests including the `\x1e`-prefixed variant
- [x] 3.3 Write `docs/docs/formats/geojsonseq.md`
- [x] 3.4 Run suite and lint
