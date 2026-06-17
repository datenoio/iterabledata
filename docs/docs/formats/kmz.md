---
title: KMZ Format
description: KMZ format support in IterableData
---

# KMZ Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `kmz` |
| Class | `KMZIterable` |
| Extensions | `.kmz` |
| Text format | Yes |
| Flat rows | No |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.kmz") as source:
    for row in source:
        print(row)
```

## Installation

```bash
pip install 'iterabledata[geospatial]'
```

## See also

- [Supported formats](/formats/)
