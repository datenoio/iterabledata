---
title: DXF Format
description: DXF format support in IterableData
---

# DXF Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `dxf` |
| Class | `DXFIterable` |
| Extensions | `.dxf` |
| Text format | No |
| Flat rows | No |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.dxf") as source:
    for row in source:
        print(row)
```

## Installation

```bash
pip install 'iterabledata[dxf]'
```

## See also

- [Supported formats](/formats/)
