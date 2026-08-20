---
title: KMZ Format
description: Zipped KML placemarks in IterableData
---

# KMZ Format

## Description

KMZ is a ZIP archive that contains a KML document (typically `doc.kml`) plus optional assets. IterableData opens the archive, locates the KML entry, and streams Placemarks as GeoJSON-like features. It is **read-only** in this release.

## File Extensions

- `.kmz` — zipped KML archives

## Implementation Details

### Reading

- Opens a `.kmz` ZIP (filename or in-memory stream bytes)
- Finds `doc.kml` / `kml.kml`, otherwise the first `.kml` member
- Parses Placemarks with `lxml` (same conversion path as KML)
- Yields GeoJSON-like features (`type`, `geometry`, `properties`); placemarks without geometry are skipped
- Loads all matching features into memory; `totals()` returns the feature count

### Writing

Writing is not supported. Use [KML](kml.md) (writable) or convert to [GeoJSON](geojson.md) / [GeoJSONSeq](geojsonseq.md).

### Key Features

- **Archive aware**: reads KML from ZIP without manual extraction
- **GeoJSON-like rows**: same feature shape as KML
- **Stream input**: can read KMZ bytes from a stream

## Usage

```python
from iterable import open_iterable

with open_iterable("places.kmz") as source:
    for feature in source:
        print(feature.get("properties"), feature["geometry"])
```

## Parameters

No format-specific `iterableargs`. Standard `open_iterable` options (`filename` / stream, codec, mode) apply. Mode must be `"r"`.

## Installation

```bash
pip install 'iterabledata[geospatial]'
pip install 'iterabledata[xml]'   # provides lxml used for KML parsing
```

KMZ is registered under the `geospatial` extra; parsing requires `lxml` (the `xml` extra).

## Limitations

1. **Read-only**
2. **Memory**: all Placemarks are loaded before iteration
3. **Requires lxml**
4. **Invalid ZIP** or missing KML entry raises `ValueError`

## Error Handling

- **ImportError**: missing `lxml` — install `iterabledata[xml]`
- **ValueError**: write mode (`mode != "r"`), invalid ZIP, or no `.kml` in the archive
- **I/O errors**: missing or unreadable path raise standard file exceptions

## Related Formats

- [KML](kml.md) — uncompressed Keyhole Markup Language (read and write)
- [GPX](gpx.md) — GPS tracks and waypoints
- [GeoJSON](geojson.md) — JSON geographic features
