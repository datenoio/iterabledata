---
title: TopoJSON Format
description: TopoJSON topology features in IterableData
---

# TopoJSON Format

Read TopoJSON topologies as GeoJSON-like features (when `topojson` is installed); write buffered geometries as a Topology on close.

## Overview

| Property | Value |
|----------|-------|
| Format id | `topojson` |
| Class | `TopoJSONIterable` |
| Extensions | `.topojson` |
| Read | Yes |
| Write | Yes |
| Extra | `topojson` (`topojson`) |
| Maturity | stable |

## Record shape

On read with the library available, Feature / FeatureCollection members. Without it (or on streaming large files via `ijson`), raw topology objects may be returned instead. Writes accept geometry dicts buffered into one `Topology` on `close()`.

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("map.topojson") as source:
    for feature in source:
        print(feature.get("type"), feature.get("geometry"))
```

Install with `pip install iterabledata[topojson]`.

## See also

- [GeoJSON](/formats/geojson) — GeoJSON features
- [MVT](/formats/mvt) — Mapbox Vector Tiles
- [Supported formats](/formats/)
