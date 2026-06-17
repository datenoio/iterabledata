---
title: GEXF Format
description: GEXF format support in IterableData
---

# GEXF Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `gexf` |
| Class | `GEXFIterable` |
| Extensions | `.gexf` |
| Text format | Yes |
| Flat rows | No |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.gexf") as source:
    for row in source:
        print(row)
```

## Installation

```bash
pip install 'iterabledata[graph]'
```

## See also

- [Supported formats](/formats/)
