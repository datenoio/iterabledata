---
title: CDF Format
description: NASA Common Data Format records in IterableData
---

# CDF Format

Read NASA Common Data Format (CDF) files as one dict per record index across variables. CDF is **read-only** in this release.

## Overview

| Property | Value |
|----------|-------|
| Format id | `cdf` |
| Class | `CDFIterable` |
| Extensions | `.cdf` |
| Read | Yes |
| Write | No |
| Extra | `cdf` (`spacepy` / NASA CDF C library) |
| Maturity | stable |

## File Extensions

- `.cdf` — NASA Common Data Format

## Implementation Details

### Reading

- Opens a local filename (or a file object with a `name` attribute); bare streams without a path are not supported
- Iterates by record index across CDF variables
- Keys are variable names; values are Python scalars or lists (NumPy/CDF types are converted)
- `list_tables()` returns variable names

### Writing

Writing is not supported. Opening with `mode="w"` raises `WriteNotSupportedError`.

### Key Features

- **Record-oriented**: one dict per CDF record index
- **Variable discovery**: `list_tables()` lists variable names
- **Native types**: scalars and arrays converted to Python types

## Usage

```python
from iterable import open_iterable

with open_iterable("data.cdf", format="cdf") as source:
    print(source.list_tables())
    for row in source:
        print(row)
```

Record shape:

```python
{"Epoch": "...", "VariableA": 1.2, "VariableB": [0.0, 1.0]}
```

## Parameters

CDF has no format-specific `iterableargs`. Pass a filename (or a named file object).

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| *(none)* | — | — | — | No format-specific parameters |

## Error Handling

- **ImportError**: Missing `spacepy` or CDF C library — install with `pip install iterabledata[cdf]` and see https://cdf.gsfc.nasa.gov for the NASA CDF C library
- **WriteNotSupportedError**: Raised for `mode="w"` (CDF is read-only)
- **ReadError**: Cannot open the file, or no filename / named file object is available
- **FileNotFoundError**: Path is wrong or the file is missing

See [Troubleshooting](/getting-started/troubleshooting) for more help.

## Installation

```bash
pip install 'iterabledata[cdf]'
```

Also requires the NASA CDF C library (https://cdf.gsfc.nasa.gov).

## Limitations

1. **Read-only**
2. **Filename (or named file object) required**
3. **Requires spacepy and the NASA CDF C library**

## Related Formats

- [NetCDF](nc.md) — NetCDF scientific arrays
- [HDF5](hdf5.md) — hierarchical arrays
