---
title: CDF Format
description: CDF format support in IterableData
---

# CDF Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `cdf` |
| Class | `CDFIterable` |
| Extensions | `.cdf` |
| Text format | No |
| Flat rows | No |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.cdf") as source:
    for row in source:
        print(row)
```

## Installation

```bash
pip install 'iterabledata[cdf]'
```

## See also

- [Supported formats](/formats/)
