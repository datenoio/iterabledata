---
title: XLSB Format
description: Excel Binary Workbook rows in IterableData
---

# XLSB Format

Read Excel Binary Workbooks (`.xlsb`) as flat row dictionaries (header from the first row).

## Overview

| Property | Value |
|----------|-------|
| Format id | `xlsb` |
| Class | `XLSBIterable` |
| Extensions | `.xlsb` |
| Read | Yes |
| Write | No |
| Extra | `xlsb` (`pyxlsb`) |
| Maturity | stable |

## Record shape

Keys come from the first sheet row (or explicit `keys`):

```python
{"name": "alpha", "value": "42"}
```

Cell values are stringified. Requires a filename (streams not supported). `list_tables()` returns sheet names.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `page` | `0` | Zero-based sheet index |
| `keys` | first row | Optional explicit column names |
| `start_line` | `0` | Rows to skip after the header |

## Usage

```python
from iterable import open_iterable

with open_iterable("data.xlsb") as source:
    for row in source:
        print(row)

with open_iterable(
    "data.xlsb",
    iterableargs={"page": 1},
) as source:
    for row in source:
        print(row)
```

Install with `pip install iterabledata[xlsb]`.

## See also

- [XLSX](/formats/xlsx) — Office Open XML workbooks
- [XLS](/formats/xls) — legacy Excel
- [Supported formats](/formats/)
