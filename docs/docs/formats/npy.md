---
title: NumPy Format
description: NumPy .npy/.npz array rows in IterableData
---

# NumPy Format

Read and write NumPy `.npy` / `.npz` arrays as flat row dictionaries.

## Overview

| Property | Value |
|----------|-------|
| Format id | `npy` (alias `npz`) |
| Class | `NumPyIterable` |
| Extensions | `.npy`, `.npz` |
| Read | Yes |
| Write | Yes |
| Extra | `npy` (`numpy`) |
| Maturity | stable |

## Record shape

| Array rank | Record |
|------------|--------|
| 1D | `{"value": scalar}` per element |
| 2D | `{"col_0": ..., "col_1": ..., ...}` per row |

Only 1D/2D arrays are supported. Requires a filename (not a stream).

## Parameters

| Parameter | Description |
|-----------|-------------|
| `array_name` | For `.npz`, array to iterate (default: first); used on write as the saved name |

`list_tables()` returns array names for `.npz` (or `None` for `.npy`). `totals()` is the leading axis length. Writes buffer rows and flush on `close()`.

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("matrix.npy") as source:
    for row in source:
        print(row)

with open_iterable("data.npz", iterableargs={"array_name": "X"}) as source:
    for row in source:
        print(row)
```

Install with `pip install iterabledata[npy]`.

## See also

- [MATLAB MAT](/formats/mat) — MATLAB variables
- [Supported formats](/formats/)
