---
title: SAM Format
description: SAM format support in IterableData
---

# SAM Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `sam` |
| Class | `SAMIterable` |
| Extensions | `.sam` |
| Text format | Yes |
| Flat rows | Yes |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.sam") as source:
    for row in source:
        print(row)
```

## Installation

```bash
pip install 'iterabledata[alignment]'
```

## See also

- [Supported formats](/formats/)
