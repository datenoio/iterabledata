---
title: NetCDF Format
description: NetCDF dimension-sliced variable records in IterableData
---

# NetCDF Format

Read NetCDF datasets as one record per index along a chosen dimension. NetCDF is **read-only** in this release.

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

## File Extensions

- `.nc` — NetCDF
- `.netcdf` — NetCDF (alias extension)

## Implementation Details

### Reading

- Opens a local filename (or a file object with a `name` attribute); bare streams are not supported
- Iterates along `dimension` (default: unlimited dimension, else the first dimension)
- Each record maps variable names to scalars or arrays for that dimension index
- Variables that do not use the target dimension are repeated on every record
- `list_tables()` lists variable names; `totals()` is the target dimension size

### Writing

Writing is not supported. Opening with `mode="w"` raises `WriteNotSupportedError`.

### Key Features

- **Dimension slicing**: walk time or another axis as records
- **Variable discovery**: `list_tables()` / `totals()`
- **Masked values**: masked scalars become `None`

## Usage

```python
from iterable import open_iterable

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

Record shape:

```python
{"time": "...", "temperature": 20.5, "lat": [...], "lon": [...]}
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `dimension` | str | unlimited, else first dim | No | Dimension name to iterate |

## Error Handling

- **ImportError**: Missing `netCDF4` — install with `pip install iterabledata[netcdf]` (pulls NumPy as needed)
- **WriteNotSupportedError**: NetCDF writing is not implemented
- **ReadError**: No filename / named file object available
- **FileNotFoundError** / netCDF4 errors: missing path or corrupt / unsupported NetCDF content

See [Troubleshooting](/getting-started/troubleshooting) for more help.

## Installation

```bash
pip install 'iterabledata[netcdf]'
```

Requires `netCDF4` (and its native NetCDF/HDF5 libraries). For broader scientific stacks you may also want related extras such as `hdf5` or `npy`.

## Limitations

1. **Read-only**
2. **Filename (or named file object) required**
3. **Requires netCDF4**
4. **Non-sliced variables are repeated** on every record (can be large)

## Related Formats

- [CDF](cdf.md) — NASA CDF
- [HDF5](hdf5.md) — hierarchical arrays
- [Supported formats](/formats/)
