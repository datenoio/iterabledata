---
title: RSS Format
description: RSS format support in IterableData
---

# RSS Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `rss` |
| Class | `FeedIterable` |
| Extensions | `.rss`, `.feed`, `.atom` |
| Text format | No |
| Flat rows | No |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.rss") as source:
    for row in source:
        print(row)
```

## Installation

```bash
pip install 'iterabledata[feed]'
```

## See also

- [Supported formats](/formats/)
