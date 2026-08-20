---
title: ARFF Format
description: Weka ARFF attribute-relation tables in IterableData
---

# ARFF Format

Read Weka ARFF (Attribute-Relation File Format) datasets as flat attribute dictionaries. ARFF is **read-only** in this release.

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

## File Extensions

- `.arff` — Weka Attribute-Relation File Format

## Implementation Details

### Reading

- Loads the full file via `liac-arff` (`arff.loads`)
- Attribute names become keys; missing values (`?`) are `None`
- Relation name is included as `_relation`
- Sparse ARFF rows are densified before yield
- `read_bulk()` uses in-memory slicing for efficiency

### Writing

Writing is not supported. `write()` / `write_bulk()` raise `WriteNotSupportedError`.

### Key Features

- **Dense and sparse** ARFF instances
- **Relation metadata** via `_relation`
- **In-memory bulk reads**

## Usage

```python
from iterable import open_iterable

with open_iterable("weather.arff") as source:
    for row in source:
        print(row)
```

Record shape:

```python
{"outlook": "sunny", "temperature": 85, "play": "no", "_relation": "weather"}
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `encoding` | str | `'utf8'` | No | Text encoding |

## Error Handling

- **ImportError**: Missing `liac-arff` — install with `pip install iterabledata[arff]` (or `pip install liac-arff`)
- **WriteNotSupportedError**: ARFF write mode is not currently supported
- **FileNotFoundError**: Path is wrong or the file is missing
- Corrupt / invalid ARFF may raise parse errors from `liac-arff`
- **UnicodeDecodeError**: Wrong encoding — set `encoding` in `iterableargs`

See [Troubleshooting](/getting-started/troubleshooting) for more help.

## Installation

```bash
pip install 'iterabledata[arff]'
```

## Limitations

1. **Read-only**
2. **Full file loaded into memory**
3. **Requires liac-arff**

## Related Formats

- [LIBSVM](libsvm.md) — sparse ML feature vectors
- [Supported formats](/formats/)
