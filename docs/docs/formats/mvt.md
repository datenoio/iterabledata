---
title: MVT Format
description: Mapbox Vector Tile features in IterableData
---

# MVT Format

Read Mapbox Vector Tiles (`.mvt` / `.pbf`) as flattened layer features.

## Overview

| Property | Value |
|----------|-------|
| Format id | `mvt` (alias `pbf`) |
| Class | `MVTIterable` |
| Extensions | `.mvt`, `.pbf` |
| Read | Yes |
| Write | No |
| Extra | `mvt` (`mapbox-vector-tile`) |
| Maturity | stable |

## Record shape

```python
{
    "layer": "roads",
    "geometry": {...},
    "properties": {"name": "Main St"},
    "type": 3,
    "id": 42,
}
```

`totals()` returns the feature count across layers. The tile is decoded in memory.

## Usage

```python
from iterable import open_iterable

with open_iterable("tile.mvt") as source:
    for feat in source:
        print(feat["layer"], feat["properties"])
```

Install with `pip install iterabledata[mvt]`.

## See also

- [GeoJSON](/formats/geojson) — JSON geographic features
- [TopoJSON](/formats/topojson) — topology-encoded maps
- [Supported formats](/formats/)
