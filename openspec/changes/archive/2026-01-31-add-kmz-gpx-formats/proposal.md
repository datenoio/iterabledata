# Change: Add KMZ and GPX Geospatial Format Support

## Why
Users need to process KMZ (KML Zipped) and GPX (GPS Exchange Format) files in streaming pipelines. KMZ is the compressed packaging of KML used by Google Earth and many GIS tools; GPX is the standard interchange format for GPS waypoints, routes, and tracks. IterableData already supports KML via `KMLIterable`; adding KMZ allows reading the common zipped variant without manual extraction. Adding GPX completes coverage of widely used geospatial/GPS formats and enables consistent row-based access to waypoints, route points, and track points.

## What Changes
- Add KMZ format support: read `.kmz` files by treating them as ZIP archives containing a root KML document (e.g. `doc.kml` or first `.kml` entry), delegating parsing to existing KML logic (stdlib `zipfile` + existing KML iterable).
- Add GPX format support: read GPX 1.0/1.1 files using lxml, exposing waypoints (`<wpt>`), route points (`<rtept>`), and track points (`<trkpt>`) as iterable records with consistent GeoJSON-like or schema-defined fields (e.g. lat, lon, ele, time, name, description).
- Register `.kmz` and `.gpx` in `iterable/helpers/detect.py` and extend `detect_file_type` for extension and, where applicable, content-based detection (e.g. KMZ as ZIP with KML inside; GPX via root element/namespace).
- Use existing dependencies where possible: `xml` extra (lxml) for GPX and for KML used by KMZ; stdlib `zipfile` for KMZ. No new optional dependency group required unless the project prefers a dedicated `gpx` or `geospatial` entry for discoverability.
- Add iterable classes in `iterable/datatypes/` (e.g. `kmz.py`, `gpx.py`) and tests in `tests/` for each format.

## Impact
- **New capabilities**: geospatial-formats (KMZ, GPX) — new spec delta under `specs/geospatial-formats`.
- **Affected specs**: New spec `openspec/changes/add-kmz-gpx-formats/specs/geospatial-formats/spec.md` with ADDED requirements for KMZ and GPX.
- **Affected code**:
  - `iterable/helpers/detect.py` (format detection, DATATYPE_REGISTRY, extension lists)
  - `iterable/datatypes/kmz.py` (new), `iterable/datatypes/gpx.py` (new)
  - `iterable/datatypes/__init__.py` (exports for KMZIterable, GPXIterable)
  - `tests/test_kmz.py`, `tests/test_gpx.py` (or `tests/test_geospatial_formats.py`)
  - Documentation (README, format docs) and optional dependency grouping in `pyproject.toml` if adding a dedicated extra
