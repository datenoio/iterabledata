---
title: LIBSVM Format
description: LIBSVM sparse labeled feature vectors in IterableData
---

# LIBSVM Format

Read and write LIBSVM sparse feature lines (`label index:value …`). No optional dependency (stdlib).

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

## File Extensions

- `.libsvm` — LIBSVM sparse labeled vectors

## Implementation Details

### Reading

- One text line per example: `<label> <index>:<value> …`
- Yields `{label_key: label, features_key: {index: value, ...}}`
- Labels that are whole numbers become `int`; otherwise `float`
- Empty lines are skipped when `skip_empty=True` (default)

### Writing

- Writes one LIBSVM line per record
- `features` may be a dict (index→value) or a dense list/tuple (1-based; zeros omitted)
- Use `write_bulk()` for fewer I/O calls

### Key Features

- **Read and write**
- **Sparse dicts**: natural ML sparse representation
- **Configurable keys**: `label_key` / `features_key`

## Usage

```python
from iterable import open_iterable

with open_iterable("train.libsvm") as source:
    for row in source:
        print(row["label"], row["features"])

with open_iterable("out.libsvm", mode="w") as dest:
    dest.write({"label": 1, "features": {1: 0.5, 3: 0.8}})
    dest.write({"label": -1, "features": [0.0, 0.3, 0.0, 0.9]})  # dense → sparse
```

Record shape:

```python
{"label": 1, "features": {1: 0.5, 3: 0.8, 5: 1.0}}
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `label_key` | str | `"label"` | No | Dict key for the label |
| `features_key` | str | `"features"` | No | Dict key for the sparse feature map |
| `encoding` | str | `"utf8"` | No | Text encoding |

## Error Handling

- **FormatParseError**: Invalid label, missing `:`, or non-numeric feature index/value
- **WriteError**: `features` is not a dict, list, or tuple
- **FileNotFoundError**: Path is wrong or the file is missing
- **UnicodeDecodeError**: Wrong encoding — set `encoding` in `iterableargs`

See [Troubleshooting](/getting-started/troubleshooting) for more help.

## Limitations

1. **Text lines only** — not a binary SVM model format
2. **Sparse convention** — indices are 1-based when writing from dense lists

## Related Formats

- [ARFF](arff.md) — Weka attribute tables
- [Supported formats](/formats/)
