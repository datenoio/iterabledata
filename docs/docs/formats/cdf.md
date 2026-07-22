---
title: CDF Format
description: NASA Common Data Format records in IterableData
---

# CDF Format

Read NASA Common Data Format (CDF) files as one dict per record index across variables.

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

## Record shape

Keys are CDF variable names; values are Python scalars or lists:

```python
{"Epoch": "...", "VariableA": 1.2, "VariableB": [0.0, 1.0]}
```

Use `list_tables()` for variable names. Requires a filename (or a named file object). Also needs the NASA CDF C library; see https://cdf.gsfc.nasa.gov.

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.cdf", format="cdf") as source:
    print(source.list_tables())
    for row in source:
        print(row)
```

Install with `pip install iterabledata[cdf]`.

## See also

- [NetCDF](/formats/nc) — NetCDF scientific arrays
- [Supported formats](/formats/)
