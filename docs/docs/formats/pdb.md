---
title: PDB Format
description: Protein Data Bank ATOM/HETATM records in IterableData
---

# PDB Format

Read and write Protein Data Bank structure files as ATOM/HETATM records.

## Overview

| Property | Value |
|----------|-------|
| Format id | `pdb` |
| Class | `PDBIterable` |
| Extensions | `.pdb` |
| Read | Yes |
| Write | Yes |
| Extra | none (stdlib) |
| Maturity | stable |

## Record shape

```python
{
    "record_type": "ATOM",
    "serial": 1,
    "name": "CA",
    "resName": "ALA",
    "chainID": "A",
    "resSeq": 1,
    "x": 1.0,
    "y": 2.0,
    "z": 3.0,
    "element": "C",
    "model": 1,
}
```

Only ATOM/HETATM lines are yielded. Write emits fixed-width ATOM/HETATM lines.

## Parameters

| Parameter | Description |
|-----------|-------------|
| `model` | Optional filter to the N-th MODEL in multi-model files |

## Usage

```python
from iterable import open_iterable

with open_iterable("protein.pdb") as source:
    for atom in source:
        print(atom["name"], atom["resName"], atom["x"], atom["y"], atom["z"])

with open_iterable("protein.pdb", iterableargs={"model": 1}) as source:
    for atom in source:
        print(atom["model"], atom["serial"])
```


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## See also

- [CIF](/formats/cif) — crystallographic atom sites
- [XYZ](/formats/xyz) — molecular coordinate tables
- [Supported formats](/formats/)
