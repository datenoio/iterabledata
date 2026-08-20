---
title: XLSB Format
description: Excel Binary Workbook rows in IterableData
---

# XLSB Format

Read Excel Binary Workbooks (`.xlsb`) as flat row dictionaries (header from the first row). XLSB is **read-only** in this release.

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

## File Extensions

- `.xlsb` — Excel Binary Workbook

## Implementation Details

### Reading

- Uses `pyxlsb.open_workbook`
- Requires a filename (streams not supported)
- Header keys come from the first sheet row unless `keys` is set
- Cell values are stringified
- `list_tables()` returns sheet names
- Select sheet with zero-based `page`; skip data rows after the header with `start_line`

### Writing

Writing is not supported. Attempting to write raises `WriteNotSupportedError`.

### Key Features

- **Multi-sheet**: choose sheet by index via `page`
- **Explicit headers**: optional `keys`
- **Row skip**: `start_line` after the header row

## Usage

```python
from iterable import open_iterable

with open_iterable("data.xlsb") as source:
    for row in source:
        print(row)

with open_iterable(
    "data.xlsb",
    iterableargs={"page": 1, "keys": ["name", "value"], "start_line": 0},
) as source:
    for row in source:
        print(row)
```

Record shape (keys from the first row or explicit `keys`):

```python
{"name": "alpha", "value": "42"}
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `page` | int | `0` | No | Zero-based sheet index |
| `keys` | list[str] | first row | No | Explicit column names (skips header extraction) |
| `start_line` | int | `0` | No | Rows to skip after the header |

## Error Handling

- **ImportError**: Missing `pyxlsb` — install with `pip install iterabledata[xlsb]`
- **ValueError**: Stream input (`XLSB requires a filename; stream is not supported`)
- **WriteNotSupportedError**: Writing XLSB is not implemented
- **FileNotFoundError** / pyxlsb errors: missing path, invalid sheet index, or corrupt workbook

See [Troubleshooting](/getting-started/troubleshooting) for more help.

## Installation

```bash
pip install 'iterabledata[xlsb]'
```

## Limitations

1. **Read-only**
2. **Filename required** (no streams)
3. **Values are strings**
4. **Requires pyxlsb**

## Related Formats

- [XLSX](xlsx.md) — Office Open XML workbooks
- [XLS](xls.md) — legacy Excel
- [Supported formats](/formats/)
