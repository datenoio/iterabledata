---
title: Microsoft Access Format
description: Microsoft Access (.mdb / .accdb) tables in IterableData
---

# Microsoft Access Format

Read Microsoft Access database tables as flat row dictionaries.

## Overview

| Property | Value |
|----------|-------|
| Format id | `mdb` (alias `accdb`) |
| Class | `AccessMDBIterable` |
| Extensions | `.mdb`, `.accdb` |
| Read | Yes |
| Write | No |
| Extra | `access` (`access_parser` or `pyodbc`) |
| Maturity | experimental |

## Parameters

| Parameter | Description |
|-----------|-------------|
| `table` | Table name (required when the database has multiple tables) |

Requires a filename. The selected table is loaded into memory. The pyodbc path needs a Microsoft Access ODBC driver (typically Windows).

## Usage

```python
from iterable import open_iterable

with open_iterable("inventory.mdb", format="mdb", iterableargs={"table": "Products"}) as source:
    for row in source:
        print(row)
```

Install with `pip install iterabledata[access]`.

## See also

- [SQLite](/formats/sqlite) — embedded SQL databases
- [DBF](/formats/dbf) — dBASE tables
- [Supported formats](/formats/)
