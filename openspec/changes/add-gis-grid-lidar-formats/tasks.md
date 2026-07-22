## 1. Shared setup

- [x] 1.1 Add descriptors and detection for `asc`/`ascii-grid`, `e00`, `las`, `bag`, and `czml`.
- [x] 1.2 Define and document row mappings for grid, point, sample, and packet modes.
- [x] 1.3 Add optional dependency extras and ImportError guidance.

## 2. Format implementations

- [x] 2.1 Implement Esri ASCII Grid / `.asc` streaming reader.
- [x] 2.2 Implement experimental ArcInfo `.e00` reader with clear unsupported-construct errors.
- [x] 2.3 Implement LAS point reader (document LAZ composition).
- [x] 2.4 Implement BAG reader with table/array listing when needed.
- [x] 2.5 Implement CZML packet iterator over JSON documents.

## 3. Tests and docs

- [x] 3.1 Add fixtures for each format (small public-domain samples).
- [x] 3.2 Add detection, malformed/nodata, optional-dependency, and memory-bounded tests.
- [x] 3.3 Document schemas, limitations, and examples.
- [x] 3.4 Run `openspec validate add-gis-grid-lidar-formats --strict`.
