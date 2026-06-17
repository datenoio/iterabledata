---
title: Libsvm Format
description: Libsvm format support in IterableData
---

# Libsvm Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `libsvm` |
| Class | `LIBSVMIterable` |
| Extensions | `.libsvm` |
| Text format | No |
| Flat rows | Yes |
| Read | Yes |
| Write | Yes |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.libsvm") as source:
    for row in source:
        print(row)
```

## See also

- [Supported formats](/formats/)
