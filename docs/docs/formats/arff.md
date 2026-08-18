---
title: ARFF Format
description: Weka ARFF attribute-relation tables in IterableData
---

# ARFF Format

Read Weka ARFF (Attribute-Relation File Format) datasets as flat attribute dictionaries.

## Overview

| Property | Value |
|----------|-------|
| Format id | `arff` |
| Class | `ARFFIterable` |
| Extensions | `.arff` |
| Read | Yes |
| Write | No |
| Extra | `arff` (`liac-arff`) |
| Maturity | stable |

## Record shape

Attribute names become keys; missing values (`?`) are `None`. The relation name is included as `_relation`:

```python
{"outlook": "sunny", "temperature": 85, "play": "no", "_relation": "weather"}
```

Sparse ARFF rows are densified before yield. The full file is loaded into memory.

## Usage

```python
from iterable import open_iterable

with open_iterable("weather.arff") as source:
    for row in source:
        print(row)
```

Install with `pip install iterabledata[arff]`.

## See also

- [LIBSVM](/formats/libsvm) — sparse ML feature vectors
- [Supported formats](/formats/)
