---
title: MATLAB MAT Format
description: MATLAB .mat variables as array row streams in IterableData
---

# MATLAB MAT Format

Read MATLAB `.mat` variables as one record per array row (or element for 1D arrays).

## Overview

| Property | Value |
|----------|-------|
| Format id | `mat` (alias `matlab`) |
| Class | `MATIterable` |
| Extensions | `.mat` |
| Read | Yes |
| Write | No |
| Extra | `mat` (`scipy` / `numpy`; v7.3 also needs `h5py`) |
| Maturity | experimental |

## Record shape

| Array rank | Record |
|------------|--------|
| 1D | `{"value": scalar}` per element |
| 2D | `{"col0": ..., "col1": ..., ...}` per row |
| 0D | `{"value": scalar}` |

Only 1D/2D arrays are iterated. Use `list_tables()` for variable names. When multiple variables exist, pass `variable` or `table`.

## Parameters

| Parameter | Description |
|-----------|-------------|
| `variable` / `table` | MAT variable name (required when multiple variables) |

Requires a filename path.

## Usage

```python
from iterable import open_iterable

with open_iterable("data.mat", format="mat", iterableargs={"variable": "data"}) as source:
    for row in source:
        print(row)  # e.g. {"col0": 1.0, "col1": 2.0}
```

Install with `pip install iterabledata[mat]`.

## See also

- [HDF5](/formats/hdf5) — hierarchical scientific arrays
- [NumPy](/formats/npy) — `.npy` / `.npz` arrays
- [Supported formats](/formats/)
