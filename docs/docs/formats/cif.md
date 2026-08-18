---
title: CIF Format
description: Crystallographic Information File atom sites in IterableData
---

# CIF Format

Read Crystallographic Information File (CIF) `_atom_site` loop rows as flat dictionaries.

## Overview

| Property | Value |
|----------|-------|
| Format id | `cif` |
| Class | `CIFIterable` |
| Extensions | `.cif` |
| Read | Yes |
| Write | No |
| Extra | none (stdlib) |
| Maturity | experimental |

## Record shape

Column names are stripped of the `_atom_site.` prefix:

```python
{"type_symbol": "O", "label_atom_id": "O1", "Cartn_x": 0.0, "Cartn_y": 0.0, "Cartn_z": 0.0}
```

Only `loop_` blocks whose columns all start with `_atom_site.` are yielded. `.` / `?` become `None`; numeric fields are coerced when possible.

## Usage

```python
from iterable import open_iterable

with open_iterable("structure.cif") as source:
    for atom in source:
        print(atom["type_symbol"], atom["Cartn_x"], atom["Cartn_y"], atom["Cartn_z"])
```

## See also

- [XYZ](/formats/xyz) — molecular coordinate tables
- [PDB](/formats/pdb) — Protein Data Bank atoms
- [Supported formats](/formats/)
