# Paimon Table Format

## Description

Apache Paimon **tables** (catalog / warehouse) via [`pypaimon`](https://pypi.org/project/pypaimon/). This is distinct from the standalone [Paimon Row](/formats/paimon-row) and [Paimon Mosaic](/formats/paimon-mosaic) **file** formats.

**Maturity**: experimental. Append-only tables (no primary keys) are supported for writes.

## Dependencies

```bash
pip install iterabledata[paimon-table]
# or
pip install iterabledata[paimon]
```

## Usage

```python
from iterable import open_iterable

warehouse = "/path/to/warehouse"

with open_iterable(warehouse, mode="w", iterableargs={
    "format": "paimon",
    "database": "demo",
    "table": "people",
    "create_table": True,
}) as dest:
    dest.write_bulk([
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ])

with open_iterable(warehouse, iterableargs={
    "format": "paimon",
    "database": "demo",
    "table": "people",
}) as source:
    print(source.list_tables())  # ['demo.people', ...]
    for row in source:
        print(row)
```

## File vs table

| Format id | What it opens |
|-----------|----------------|
| `paimon` | Warehouse/catalog table |
| `paimon_row` / `.row` | Standalone Row file |
| `paimon_mosaic` / `.mosaic` | Standalone Mosaic file |

## Parameters

| Parameter | Description |
|-----------|-------------|
| `format` | `paimon` |
| `database` | Database name (default `default`) |
| `table` | Table name |
| `columns` | Optional projection |
| `create_table` | Create append-only table on write |
| `batch_size` | Writer flush threshold |


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## See Also

- [PyPaimon](https://paimon.apache.org/docs/master/pypaimon/)
- [Paimon Row](/formats/paimon-row)
- [Paimon Mosaic](/formats/paimon-mosaic)
