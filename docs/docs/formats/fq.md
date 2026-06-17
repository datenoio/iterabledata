---
title: FQ Format
description: FQ format support in IterableData
---

# FQ Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `fq` |
| Class | `FASTQIterable` |
| Extensions | `.fq`, `.fastq` |
| Text format | Yes |
| Flat rows | Yes |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.fq") as source:
    for row in source:
        print(row)
```

## See also

- [Supported formats](/formats/)
