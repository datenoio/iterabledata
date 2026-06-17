---
title: NPY Format
description: NPY format support in IterableData
---

# NPY Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `npy` |
| Class | `NumPyIterable` |
| Extensions | `.npy`, `.npz` |
| Text format | No |
| Flat rows | Yes |
| Read | Yes |
| Write | Yes |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.npy") as source:
    for row in source:
        print(row)
```

## See also

- [Supported formats](/formats/)
