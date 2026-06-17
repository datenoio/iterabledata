---
title: MVT Format
description: MVT format support in IterableData
---

# MVT Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `mvt` |
| Class | `MVTIterable` |
| Extensions | `.mvt`, `.pbf` |
| Text format | No |
| Flat rows | No |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.mvt") as source:
    for row in source:
        print(row)
```

## Installation

```bash
pip install 'iterabledata[mvt]'
```

## See also

- [Supported formats](/formats/)
