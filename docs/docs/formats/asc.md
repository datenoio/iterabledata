---
title: Esri ASCII Grid Format
description: Esri ASCII Grid (.asc) support in IterableData
---

# Esri ASCII Grid Format

Stream Esri ASCII Grid rasters as cell or row records without loading the full grid first.

## Overview

| Property | Value |
|----------|-------|
| Format id | `asc` (aliases `ascii-grid`, `asciigrid`) |
| Class | `ASCIIGridIterable` |
| Extensions | `.asc` |
| Read | Yes |
| Write | Yes (cell mode) |
| Extra | none |

## Modes

- **cell** (default): one record per cell with `row`, `col`, `x`, `y`, `value` (nodata skipped).
- **row**: one record per grid row with `row` and `values` (includes nodata markers).

```python
from iterable.helpers.detect import open_iterable

with open_iterable("dem.asc") as source:
    for cell in source:
        print(cell["x"], cell["y"], cell["value"])

with open_iterable("dem.asc", iterableargs={"mode": "row"}) as source:
    for row in source:
        print(row["row"], len(row["values"]))
```

## See also

- [LAS](/formats/las) — LiDAR points
- [BAG](/formats/bag) — bathymetric grids
- [Supported formats](/formats/)
