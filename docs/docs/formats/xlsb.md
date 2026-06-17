---
title: XLSB Format
description: XLSB format support in IterableData
---

# XLSB Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `xlsb` |
| Class | `XLSBIterable` |
| Extensions | `.xlsb` |
| Text format | No |
| Flat rows | Yes |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.xlsb") as source:
    for row in source:
        print(row)
```

## Installation

```bash
pip install 'iterabledata[xlsb]'
```

## See also

- [Supported formats](/formats/)
