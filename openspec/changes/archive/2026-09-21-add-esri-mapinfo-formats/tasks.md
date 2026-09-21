## 1. Registry and dependencies

- [x] 1.1 Add format descriptors/aliases for `fgdb`/`gdb` and `mif` in the format registry.
- [x] 1.2 Add optional geospatial dependency extra and missing-dependency ImportError messaging.
- [x] 1.3 Wire extension detection (and directory/magic detection for FileGDB where practical).

## 2. File Geodatabase

- [x] 2.1 Implement FileGDB iterable with layer listing via `list_tables()`.
- [x] 2.2 Require explicit layer selection when multiple layers exist; document default when exactly one layer is present.
- [x] 2.3 Stream GeoJSON-like feature rows with bounded memory behavior.
- [x] 2.4 Decide and document v1 write support (read-only is acceptable).

## 3. MapInfo MIF

- [x] 3.1 Implement MIF/MID reader yielding feature rows.
- [x] 3.2 Handle missing MID and malformed geometry with clear errors.
- [x] 3.3 Add write support if the chosen backend supports round-trips; otherwise mark read-only.

## 4. Tests and docs

- [x] 4.1 Add fixtures from representative open-data samples (multi-layer GDB, MIF+MID).
- [x] 4.2 Add detection, optional-dependency, empty/malformed, and streaming tests.
- [x] 4.3 Document formats, layer selection, limitations, and examples.
- [x] 4.4 Run `openspec validate add-esri-mapinfo-formats --strict`.
