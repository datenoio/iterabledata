---
title: BAM Format
description: BAM format support in IterableData
---

# BAM Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `bam` |
| Class | `BAMIterable` |
| Extensions | `.bam` |
| Text format | No |
| Flat rows | Yes |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.bam") as source:
    for row in source:
        print(row)
```

## Installation

```bash
pip install 'iterabledata[alignment]'
```

## See also

- [Supported formats](/formats/)
