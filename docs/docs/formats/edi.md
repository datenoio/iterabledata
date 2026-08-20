---
title: EDI Format
description: EDI X12/EDIFACT segment streams in IterableData
---

# EDI Format

Read EDI transaction sets as segment records (documented X12/EDIFACT subset).

## Overview

| Property | Value |
|----------|-------|
| Format id | `edi` |
| Class | `EDIIterable` |
| Extensions | `.edi` |
| Read | Yes |
| Write | No |
| Extra | none |
| Maturity | experimental |

## Record shape

```python
{"segment_id": "BEG", "elements": ["00", "SA", "PO123", "20240115"]}
```

Segment terminator defaults to `~` or newline; element separator is detected from common `*` / `+` conventions.

## Usage

```python
from iterable import open_iterable

with open_iterable("order.edi") as source:
    for segment in source:
        if segment["segment_id"] == "BEG":
            print(segment["elements"])
```

## See also

- [Supported formats](/formats/)

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `encoding` | str | `'utf8'` | No | Passed via `iterableargs`. |

