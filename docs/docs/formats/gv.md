---
title: GV Format
description: GV format support in IterableData
---

# GV Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `gv` |
| Class | `DOTIterable` |
| Extensions | `.gv`, `.dot` |
| Text format | Yes |
| Flat rows | No |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.gv") as source:
    for row in source:
        print(row)
```

## Installation

```bash
pip install 'iterabledata[graph]'
```

## See also

- [Supported formats](/formats/)
