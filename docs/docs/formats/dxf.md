---
title: DXF Format
description: AutoCAD DXF modelspace entities in IterableData
---

# DXF Format

Read AutoCAD DXF drawings as one record per modelspace entity.

## Overview

| Property | Value |
|----------|-------|
| Format id | `dxf` |
| Class | `DXFIterable` |
| Extensions | `.dxf` |
| Read | Yes |
| Write | No |
| Extra | `dxf` (`ezdxf`) |
| Maturity | stable |

## Record shape

Common fields plus geometry keyed by entity type (`LINE`, `CIRCLE`, `ARC`, `POINT`, `TEXT`, `LWPOLYLINE`, `POLYLINE`, …):

```python
{
    "dxftype": "LINE",
    "layer": "0",
    "color": 256,
    "handle": "1A",
    "start": (0.0, 0.0, 0.0),
    "end": (1.0, 0.0, 0.0),
}
```

`totals()` returns the modelspace entity count.

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("drawing.dxf") as source:
    for entity in source:
        print(entity["dxftype"], entity.get("layer"))
```

Install with `pip install iterabledata[dxf]`.

## See also

- [Supported formats](/formats/)
