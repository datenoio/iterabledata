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
from iterable.helpers.detect import open_iterable

with open_iterable("molecule.xyz") as source:
    for row in source:
        print(row["element"], row["x"], row["y"], row["z"])
```

## See also

- [CIF](/formats/cif) — crystallographic atom sites
- [PDB](/formats/pdb) — Protein Data Bank atoms
- [Supported formats](/formats/)
