---
title: ARFF Format
description: ARFF format support in IterableData
---

# ARFF Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `arff` |
| Class | `ARFFIterable` |
| Extensions | `.arff` |
| Text format | Yes |
| Flat rows | Yes |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.arff") as source:
    for row in source:
        print(row)
```

## Installation

```bash
pip install 'iterabledata[arff]'
```

## See also

- [Supported formats](/formats/)
