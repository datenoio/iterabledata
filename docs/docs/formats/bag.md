---
title: BAG Bathymetry
description: BAG bathymetric HDF5 grids in IterableData
---

# BAG Bathymetry

Stream BAG (Bathymetric Attributed Grid) HDF5 products as one record per grid cell.

## Overview

| Property | Value |
|----------|-------|
| Format id | `bag` |
| Class | `BAGIterable` |
| Extensions | `.bag` |
| Read | Yes |
| Write | No |
| Extra | `hdf5` (`h5py`) |
| Maturity | experimental |

## Record shape

```python
{"row": 0, "col": 0, "value": 1.0}
```

By default the first elevation dataset under `/BAG_root` is used. Override with `dataset` or `table`.

## Usage

```python
from iterable import open_iterable

with open_iterable("survey.bag", format="bag") as source:
    for cell in source:
        print(cell["row"], cell["col"], cell["value"])

with open_iterable(
    "survey.bag",
    format="bag",
    iterableargs={"dataset": "/BAG_root/elevation"},
) as source:
    for cell in source:
        print(cell)
```

Requires a filename (not a stream). Install with `pip install iterabledata[hdf5]`.

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `dataset` | str | first elevation under `/BAG_root` | No | HDF5 dataset path to stream |
| `table` | str | same as `dataset` | No | Alias for `dataset` |

Pass via `iterableargs`, for example `iterableargs={"dataset": "/BAG_root/elevation"}`.

## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Read-only**: opening with `mode="w"` raises `WriteNotSupportedError` or `ValueError`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## See also

- [ASCII Grid](/formats/asc) — Esri ASCII rasters
- [NetCDF](/formats/nc) — scientific gridded data
- [Supported formats](/formats/)
