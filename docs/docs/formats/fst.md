---
title: fst Format
description: R fst columnar data frames in IterableData
---

# fst Format

Read R [fst](https://www.fstpackage.org/) columnar on-disk data frames as flat row dictionaries.

## Overview

| Property | Value |
|----------|-------|
| Format id | `fst` |
| Class | `FSTIterable` |
| Extensions | `.fst` |
| Read | Yes |
| Write | No |
| Extra | `fst` (`fst` or `rfst` binding) |
| Maturity | experimental |

## Parameters

| Parameter | Description |
|-----------|-------------|
| `columns` | Optional column subset passed to the fst reader when supported |

The entire frame is loaded into memory (not streaming). Requires a filename path.

## Usage

```python
from iterable import open_iterable

with open_iterable("frame.fst", format="fst") as source:
    for row in source:
        print(row)

with open_iterable(
    "frame.fst",
    format="fst",
    iterableargs={"columns": ["id", "value"]},
) as source:
    for row in source:
        print(row)
```

Install with `pip install iterabledata[fst]` (or install a compatible `fst` / `rfst` binding).

## See also

- [RDS](/formats/rds) / [RData](/formats/rdata) — R serialized objects
- [Parquet](/formats/parquet) — columnar storage
- [Supported formats](/formats/)
