---
title: TRIG Format
description: TRIG format support in IterableData
---

# TRIG Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `trig` |
| Class | `TriGIterable` |
| Extensions | `.trig` |
| Text format | Yes |
| Flat rows | No |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.trig") as source:
    for row in source:
        print(row)
```

## Installation

```bash
pip install 'iterabledata[rdf]'
```

## See also

- [Supported formats](/formats/)
