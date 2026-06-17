---
title: FA Format
description: FA format support in IterableData
---

# FA Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `fa` |
| Class | `FASTAIterable` |
| Extensions | `.fa`, `.fasta`, `.fna`, `.faa` |
| Text format | Yes |
| Flat rows | Yes |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.fa") as source:
    for row in source:
        print(row)
```

## See also

- [Supported formats](/formats/)
