---
title: GPX Format
description: GPX waypoints, routes, and tracks in IterableData
---

# GPX Format

Read GPX 1.0/1.1 waypoints, route points, and track points as coordinate records.

## Overview

| Property | Value |
|----------|-------|
| Format id | `gpx` |
| Class | `GPXIterable` |
| Extensions | `.gpx` |
| Read | Yes |
| Write | No |
| Extra | `xml` (`lxml`) |
| Maturity | stable |

## Record shape

```python
{
    "lat": 37.77,
    "lon": -122.42,
    "point_type": "track",  # waypoint | route | track
    "ele": 10.0,
    "time": "2024-01-01T12:00:00Z",
    "name": "Point A",
}
```

Optional child fields (`ele`, `time`, `name`, `description`, …) appear when present. `totals()` returns the point count.

## Usage

```python
from iterable import open_iterable

with open_iterable("hike.gpx") as source:
    for pt in source:
        print(pt["point_type"], pt["lat"], pt["lon"])
```

Install with `pip install iterabledata[xml]`.

## See also

- [KML](/formats/kml) — Keyhole Markup Language
- [KMZ](/formats/kmz) — zipped KML
- [Supported formats](/formats/)
