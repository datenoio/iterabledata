---
title: LAS Format
description: LAS LiDAR point clouds in IterableData
---

# LAS Format

Stream LAS LiDAR point clouds as one record per point.

## Overview

| Property | Value |
|----------|-------|
| Format id | `las` |
| Class | `LASIterable` |
| Extensions | `.las` |
| Read | Yes |
| Write | No |
| Extra | `lidar` (`laspy`) |
| Maturity | experimental |

## Record shape

```python
{
    "x": 1.0,
    "y": 2.0,
    "z": 3.0,
    "intensity": 100,
    "classification": 2,
    "return_number": 1,
}
```

`intensity`, `classification`, and `return_number` may be `None` when absent from the point format.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `chunk_size` | `50000` | laspy chunk iterator size |

Requires a filename. `totals()` returns the point count. Streaming via chunked reads.

## Usage

```python
from iterable import open_iterable

with open_iterable("cloud.las", format="las") as source:
    print(f"points: {source.totals()}")
    for pt in source:
        print(pt["x"], pt["y"], pt["z"], pt["classification"])
```

Install with `pip install iterabledata[lidar]`.

## See also

- [ASCII Grid](/formats/asc) — raster grids
- [XYZ](/formats/xyz) — coordinate tables
- [Supported formats](/formats/)
