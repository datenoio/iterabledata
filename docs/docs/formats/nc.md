---
title: NC Format
description: NC format support in IterableData
---

# NC Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `nc` |
| Class | `NetCDFIterable` |
| Extensions | `.nc`, `.netcdf` |
| Text format | No |
| Flat rows | No |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.nc") as source:
    for row in source:
        print(row)
```

## Installation

```bash
pip install 'iterabledata[netcdf]'
```

## See also

- [Supported formats](/formats/)
