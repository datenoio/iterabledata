---
title: LIBSVM Format
description: LIBSVM sparse labeled feature vectors in IterableData
---

# LIBSVM Format

Read and write LIBSVM sparse feature lines (`label index:value …`).

## Overview

| Property | Value |
|----------|-------|
| Format id | `libsvm` |
| Class | `LIBSVMIterable` |
| Extensions | `.libsvm` |
| Read | Yes |
| Write | Yes |
| Extra | none (stdlib) |
| Maturity | stable |

## Record shape

```python
{"label": 1, "features": {1: 0.5, 3: 0.8, 5: 1.0}}
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `label_key` | `label` | Dict key for the label |
| `features_key` | `features` | Dict key for the sparse feature map |

On write, `features` may be a dict (index→value) or a dense list/tuple (1-based; zeros omitted).

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("train.libsvm") as source:
    for row in source:
        print(row["label"], row["features"])

with open_iterable("out.libsvm", mode="w") as dest:
    dest.write({"label": 1, "features": {1: 0.5, 3: 0.8}})
```

## See also

- [ARFF](/formats/arff) — Weka attribute tables
- [Supported formats](/formats/)
