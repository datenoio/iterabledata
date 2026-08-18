# DuckLake Format

## Description

DuckLake is an open lakehouse table format that stores metadata in a SQL catalog (DuckDB, SQLite, Postgres, or MySQL) and data as Parquet files. IterableData integrates via [`pyducklake`](https://pypi.org/project/pyducklake/).

**Maturity**: experimental.

## Detection

DuckLake does **not** hijack ordinary `.duckdb` database files. Always pass `format="ducklake"`.

## Dependencies

```bash
pip install iterabledata[ducklake]
```

## Usage

```python
from iterable import open_iterable

meta = "meta.duckdb"
data_path = "./data"

with open_iterable(meta, mode="w", iterableargs={
    "format": "ducklake",
    "table": "events",
    "data_path": data_path,
    "create_table": True,
}) as dest:
    dest.write_bulk([
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ])

with open_iterable(meta, iterableargs={
    "format": "ducklake",
    "table": "events",
    "data_path": data_path,
}) as source:
    print(source.list_tables())
    for row in source:
        print(row)
```

## Parameters

| Parameter | Description |
|-----------|-------------|
| `format` | Must be `ducklake` |
| `table` / `table_name` | Table id (`events` or `main.events`) |
| `data_path` | Parquet data directory |
| `create_table` | Create table on write when missing |
| `write_mode` | `append` (default), `overwrite`, `error` |
| `batch_size` | Writer flush threshold |

## See Also

- [DuckLake](https://ducklake.select/)
- [Delta Lake](/formats/delta)
- [Paimon tables](/formats/paimon)
