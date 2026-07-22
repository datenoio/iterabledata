---
title: NetCDF Format
description: NetCDF dimension-sliced variable records in IterableData
---

# NetCDF Format

Read NetCDF datasets as one record per index along a chosen dimension.

## Overview

| Property | Value |
|----------|-------|
| Format id | `nc` (alias `netcdf`) |
| Class | `NetCDFIterable` |
| Extensions | `.nc`, `.netcdf` |
| Read | Yes |
| Write | No |
| Extra | `netcdf` (`netCDF4`) |
| Maturity | stable |

## Record shape

Keys are variable names; values are scalars or arrays for that dimension index:

```python
{"time": "...", "temperature": 20.5, "lat": [...], "lon": [...]}
```

## Parameters

| Parameter | Description |
|-----------|-------------|
| `dimension` | Dimension to iterate (default: unlimited, else first) |

Requires a filename (or a named file object). `list_tables()` lists variables; `totals()` is the target dimension size.

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("climate.nc", format="nc") as source:
    print(source.list_tables())
    for row in source:
        print(row)

with open_iterable(
    "climate.nc",
    format="nc",
    iterableargs={"dimension": "time"},
) as source:
    for row in source:
        print(row)
```

Install with `pip install iterabledata[netcdf]`.

## See also

- [CDF](/formats/cdf) — NASA CDF
- [HDF5](/formats/hdf5) — hierarchical arrays
- [Supported formats](/formats/)
