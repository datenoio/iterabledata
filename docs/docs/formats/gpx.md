---
title: GPX Format
description: GPX format support in IterableData
---

# GPX Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `gpx` |
| Class | `GPXIterable` |
| Extensions | `.gpx` |
| Text format | Yes |
| Flat rows | No |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.gpx") as source:
    for row in source:
        print(row)
```

## See also

- [Supported formats](/formats/)
