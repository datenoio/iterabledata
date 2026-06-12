## 1. Dependencies and project config
- [x] 1.1 Use existing `xml` (lxml) extra for GPX and for KML used by KMZ; no new optional dependency required for parsing. Optionally add a `geospatial` or `gpx` extra in `pyproject.toml` for discoverability if the project prefers.
- [x] 1.2 Document KMZ and GPX in README and format docs; include in `all` or relevant aggregate extra if applicable.

## 2. KMZ format
- [x] 2.1 Implement `KMZIterable` in `iterable/datatypes/kmz.py`: open `.kmz` as ZIP, locate root KML (e.g. `doc.kml` or first `.kml` entry), delegate to KML parsing logic (reuse or call into existing KML iterable/parsing).
- [x] 2.2 Register `.kmz` in `iterable/helpers/detect.py` and DATATYPE_REGISTRY; add content-based detection for KMZ (ZIP with KML inside) if applicable.
- [x] 2.3 Export `KMZIterable` from `iterable/datatypes/__init__.py`.
- [x] 2.4 Add tests in `tests/test_kmz.py` (or `tests/test_geospatial_formats.py`) for read, automatic detection, and edge cases (missing doc.kml, multiple KML files).

## 3. GPX format
- [x] 3.1 Implement `GPXIterable` in `iterable/datatypes/gpx.py` using lxml: parse GPX 1.0/1.1, yield records for waypoints (`<wpt>`), route points (`<rtept>`), and track points (`<trkpt>`) with consistent fields (e.g. lat, lon, ele, time, name, description, type).
- [x] 3.2 Register `.gpx` in `iterable/helpers/detect.py` and DATATYPE_REGISTRY; add content-based detection (root element/namespace) if applicable.
- [x] 3.3 Export `GPXIterable` from `iterable/datatypes/__init__.py`.
- [x] 3.4 Add tests in `tests/test_gpx.py` (or `tests/test_geospatial_formats.py`) for read, automatic detection, waypoints/routes/tracks, and missing lxml dependency.

## 4. Documentation and capability registry
- [x] 4.1 Update README and format documentation to list KMZ and GPX; link to geospatial-formats spec or format docs.
- [x] 4.2 Ensure new formats are exposed via format capability APIs if the project has a capability registry (e.g. `get_format_capabilities`).
