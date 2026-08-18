---
title: File Geodatabase Format
description: ESRI File Geodatabase support in IterableData
---

# File Geodatabase Format

Read ESRI File Geodatabase (`.gdb` / `.fgdb`) layers as GeoJSON-like Features via Fiona’s OpenFileGDB driver.

## Overview

| Property | Value |
|----------|-------|
| Format id | `fgdb` (alias `gdb`) |
| Class | `FileGDBIterable` |
| Extensions / paths | `.gdb` directory, `.fgdb` label |
| Read | Yes |
| Write | No (v1) |
| Extra | `geospatial` (`fiona`) |
| Maturity | experimental |

## Usage

```python
from iterable import open_iterable

# List layers when multiple exist
with open_iterable("parcels.gdb", format="fgdb") as source:
    print(source.list_tables())

with open_iterable("parcels.gdb", format="fgdb", iterableargs={"layer": "parcels"}) as source:
    for feature in source:
        print(feature["geometry"]["type"], feature["properties"])
```

## Installation

```bash
pip install 'iterabledata[geospatial]'
```

Requires a Fiona build with the OpenFileGDB driver.

## See also

- [MapInfo MIF](/formats/mif)
- [GeoPackage](/formats/geopackage)
- [Shapefile](/formats/shapefile)
- [Supported formats](/formats/)
