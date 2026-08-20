---
title: MapInfo MIF Format
description: MapInfo Interchange Format (MIF/MID) features in IterableData
---

# MapInfo MIF Format

Read MapInfo Interchange Format (MIF/MID) vector features via Fiona as GeoJSON-like Feature dicts.

## Overview

| Property | Value |
|----------|-------|
| Format id | `mif` |
| Class | `MapInfoIterable` |
| Extensions | `.mif` (companion `.mid` handled by the driver) |
| Read | Yes |
| Write | No |
| Extra | `geospatial` (`fiona`) |
| Maturity | experimental |

## Record shape

```python
{
    "type": "Feature",
    "id": "...",
    "properties": {...},
    "geometry": {"type": "Polygon", "coordinates": [...]},
}
```

Requires a filename (not a stream). Uses Fiona's `MapInfo File` driver with streaming feature iteration.

## Usage

```python
from iterable import open_iterable

with open_iterable("parcels.mif", format="mif") as source:
    for feature in source:
        print(feature["id"], feature["geometry"]["type"], feature["properties"])
```

Install with `pip install iterabledata[geospatial]`.

## Parameters

No format-specific `iterableargs`. A filesystem path is required (streams and codecs are not supported). Companion `.mid` attribute files are resolved by Fiona's MapInfo driver when co-located.

## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Read-only**: opening with `mode="w"` raises `WriteNotSupportedError` or `ValueError`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## See also

- [Shapefile](/formats/shapefile) — ESRI shapefiles
- [File Geodatabase](/formats/fgdb) — ESRI FileGDB
- [GeoPackage](/formats/geopackage) — OGC GeoPackage
- [Supported formats](/formats/)
