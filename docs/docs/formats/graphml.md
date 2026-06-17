---
title: Graphml Format
description: Graphml format support in IterableData
---

# Graphml Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `graphml` |
| Class | `GraphMLIterable` |
| Extensions | `.graphml` |
| Text format | Yes |
| Flat rows | No |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.graphml") as source:
    for row in source:
        print(row)
```

## Installation

```bash
pip install 'iterabledata[graph]'
```

## See also

- [Supported formats](/formats/)
