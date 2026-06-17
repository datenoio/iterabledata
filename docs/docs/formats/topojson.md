---
title: Topojson Format
description: Topojson format support in IterableData
---

# Topojson Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `topojson` |
| Class | `TopoJSONIterable` |
| Extensions | `.topojson` |
| Text format | No |
| Flat rows | No |
| Read | Yes |
| Write | Yes |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.topojson") as source:
    for row in source:
        print(row)
```

## Installation

```bash
pip install 'iterabledata[topojson]'
```

## See also

- [Supported formats](/formats/)
