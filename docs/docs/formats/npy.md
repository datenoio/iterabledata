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

## File Extensions

- `.npy` — single NumPy array
- `.npz` — compressed archive of named arrays

## Implementation Details

### Reading

- Requires a filename (not a stream)
- **1D**: one `{"value": scalar}` per element
- **2D**: one `{"col_0": ..., "col_1": ..., ...}` per row
- Higher-rank arrays raise `FormatNotSupportedError`
- For `.npz`, choose the array with `array_name` (default: first); `list_tables()` lists names
- `totals()` is the leading axis length

### Writing

- Buffers rows and flushes on `close()`
- Dict rows become a 2D float array (sorted keys as columns; missing → `0.0`)
- `.npz` writes use `array_name` (default `"data"`) with `np.savez_compressed`
- Requires a filename

### Key Features

- **Read and write**
- **`.npy` and `.npz`**
- **Named arrays**: `array_name` / `list_tables()` for archives

## Usage

```python
from iterable import open_iterable

with open_iterable("matrix.npy") as source:
    for row in source:
        print(row)

with open_iterable("data.npz", iterableargs={"array_name": "X"}) as source:
    for row in source:
        print(row)

with open_iterable("out.npy", mode="w") as dest:
    dest.write({"col_0": 1.0, "col_1": 2.0})
    dest.write({"col_0": 3.0, "col_1": 4.0})
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `array_name` | str | first array / `"data"` on write | No | For `.npz`, array to iterate; on write, saved array name |

## Error Handling

- **ImportError**: Missing NumPy — install with `pip install iterabledata[npy]`
- **ValueError**: Stream read (`NumPy file reading requires filename`), or unknown `array_name` in `.npz`
- **FormatNotSupportedError**: Empty `.npz`, or array rank other than 1D/2D
- **WriteError**: Write without a filename
- **FileNotFoundError**: Path is wrong or the file is missing

See [Troubleshooting](/getting-started/troubleshooting) for more help.

## Installation

```bash
pip install 'iterabledata[npy]'
```

## Limitations

1. **Only 1D and 2D arrays** for iteration
2. **Filename required** (no streams)
3. **Write buffers until close**
4. **Requires NumPy**

## Related Formats

- [MATLAB MAT](mat.md) — MATLAB variables
- [HDF5](hdf5.md) — hierarchical arrays
- [Supported formats](/formats/)
