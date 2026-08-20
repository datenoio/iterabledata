---
title: XYZ Format
description: XYZ molecular and point coordinate tables in IterableData
---

# XYZ Format

Read and write whitespace-delimited XYZ coordinate tables (molecular or point clouds).

## Overview

| Property | Value |
|----------|-------|
| Format id | `xyz` |
| Class | `XYZIterable` |
| Extensions | `.xyz` |
| Text format | Yes |
| Flat rows | Yes |
| Read | Yes |
| Write | Yes |
| Extra | none (stdlib) |

## Record shape

Each data row yields:

```python
{"element": "O", "x": 0.0, "y": 0.0, "z": 0.0}
```

Optional trailing fields become `extra_0`, `extra_1`, …. An optional atom-count header and comment line are skipped on read and written on write.

## Usage

```python
from iterable import open_iterable

with open_iterable("molecule.xyz") as source:
    for row in source:
        print(row["element"], row["x"], row["y"], row["z"])
```


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## See also

- [CIF](/formats/cif) — crystallographic atom sites
- [PDB](/formats/pdb) — Protein Data Bank atoms
- [Supported formats](/formats/)

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `encoding` | str | `'utf-8'` | No | Passed via `iterableargs`. |

