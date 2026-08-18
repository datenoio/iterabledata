---
title: Lotus 1-2-3 Format
description: Lotus 1-2-3 / WK1 spreadsheet rows in IterableData
---

# Lotus 1-2-3 Format

Read Lotus 1-2-3 / WK1 spreadsheet rows as flat dictionaries (experimental minimal BIFF parser).

## Overview

| Property | Value |
|----------|-------|
| Format id | `123` (aliases `wk1`, `wks`) |
| Class | `Lotus123Iterable` |
| Extensions | `.123`, `.wk1`, `.wks` |
| Read | Yes |
| Write | No |
| Extra | none (optional `pylotus` if installed) |
| Maturity | experimental |

## Record shape

One dict per spreadsheet row. When `header=True` (default) and row 0 contains string labels, those become column keys:

```python
{"name": "alpha", "value": 42}
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `header` | `True` | Use first-row labels as keys when detected |

Loads the workbook into memory. Supports LABEL / INTEGER / NUMBER cells in the minimal WK1 subset.

## Usage

```python
from iterable import open_iterable

with open_iterable("sheet.wk1", format="123") as source:
    for row in source:
        print(row)
```

## See also

- [XLS](/formats/xls) / [XLSX](/formats/xlsx) — Excel workbooks
- [ODS](/formats/ods) — OpenDocument spreadsheets
- [Supported formats](/formats/)
