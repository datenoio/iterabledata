---
title: TRIX Format
description: TRIX format support in IterableData
---

# TRIX Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `trix` |
| Class | `TriXIterable` |
| Extensions | `.trix` |
| Text format | Yes |
| Flat rows | No |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.trix") as source:
    for row in source:
        print(row)
```

## Installation

```bash
pip install 'iterabledata[rdf]'
```

## See also

- [Supported formats](/formats/)
