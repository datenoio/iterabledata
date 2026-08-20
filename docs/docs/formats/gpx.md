---
title: GPX Format
description: GPX waypoints, routes, and tracks in IterableData
---

# GPX Format

## Description

GPX (GPS Exchange Format) is an XML standard for waypoints, routes, and tracks used by GPS devices and mapping apps. IterableData reads GPX 1.0/1.1 and yields one coordinate record per `wpt`, `rtept`, or `trkpt`. It is **read-only** in this release.

## File Extensions

- `.gpx` — GPS Exchange Format files

## Implementation Details

### Reading

- Parses the GPX document with `lxml` (namespace-agnostic tag matching)
- Collects waypoints (`wpt`), route points (`rtept`), and track points (`trkpt`)
- Each record includes `lat`, `lon`, `point_type` (`waypoint` | `route` | `track`), plus optional fields (`ele`, `time`, `name`, `description`, …)
- Loads all points into memory; `totals()` returns the point count

### Writing

Writing is not supported. Export tracks as [GeoJSON](geojson.md) or [KML](kml.md) when you need writeable geospatial output.

### Key Features

- **Point types**: distinguishes waypoint, route, and track points
- **Optional metadata**: elevation, time, name, description, and common GPX child tags when present
- **Namespace tolerant**: works with typical GPX 1.0/1.1 namespaces

## Usage

```python
from iterable import open_iterable

with open_iterable("hike.gpx") as source:
    for pt in source:
        print(pt["point_type"], pt["lat"], pt["lon"], pt.get("ele"))
```

## Parameters

No format-specific `iterableargs`. Mode must be `"r"`.

## Installation

```bash
pip install 'iterabledata[xml]'
```

Requires `lxml`.

## Limitations

1. **Read-only**
2. **Memory**: all points are loaded before iteration
3. **Requires lxml**
4. Points without valid `lat`/`lon` are skipped

## Error Handling

- **ImportError**: missing `lxml` — install `iterabledata[xml]`
- **ValueError**: write mode (`mode != "r"`)
- **Parse / I/O issues**: malformed XML or unreadable files may yield an empty iterator or raise standard I/O exceptions

## Related Formats

- [KML](kml.md) — Keyhole Markup Language
- [KMZ](kmz.md) — zipped KML
- [GeoJSON](geojson.md) — JSON geographic features
