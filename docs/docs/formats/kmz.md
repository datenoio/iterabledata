---
title: KMZ Format
description: Zipped KML placemarks in IterableData
---

# KMZ Format

Read KMZ archives (ZIP containing KML) as GeoJSON-like Placemark features.

## Overview

| Property | Value |
|----------|-------|
| Format id | `kmz` |
| Class | `KMZIterable` |
| Extensions | `.kmz` |
| Read | Yes |
| Write | No |
| Extra | `geospatial` (requires `lxml`) |
| Maturity | stable |

## Record shape

Same GeoJSON-like features as KML (`type`, `geometry`, `properties`). Placemarks without geometry are skipped. `totals()` returns the feature count.

## Usage

```python
from iterable import open_iterable

with open_iterable("places.kmz") as source:
    for feature in source:
        print(feature["geometry"], feature.get("properties"))
```

Install with `pip install iterabledata[geospatial]` (parsing also needs `lxml`, e.g. `pip install iterabledata[xml]`).

## See also

- [KML](/formats/kml) — uncompressed KML
- [GPX](/formats/gpx) — GPS tracks
- [Supported formats](/formats/)
