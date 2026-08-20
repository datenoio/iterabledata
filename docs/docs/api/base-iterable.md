---
sidebar_position: 5
title: BaseIterable Methods
description: Methods available on all iterable objects
---

# BaseIterable Methods

All iterable objects returned by `open_iterable()` inherit from `BaseIterable` and provide a consistent interface for reading and writing data.

## Reading Methods

### `read(skip_empty: bool = True) -> dict`

Read a single record from the iterable.

**Parameters:**
- `skip_empty` (bool): Skip empty records. Default: `True`

**Returns:** Dictionary representing a single record, or raises `StopIteration` when no more records.

**Example:**
```python
with open_iterable('data.csv') as source:
    record = source.read()
    print(record)
```

### `read_bulk(num: int = 1000) -> list[dict]`

Read multiple records at once for better performance.

**Parameters:**
- `num` (int): Number of records to read. Default: `1000`

**Returns:** List of dictionaries representing records.

**Example:**
```python
with open_iterable('data.jsonl') as source:
    batch = source.read_bulk(10000)
    for record in batch:
        process(record)
```

### `__iter__()` and `__next__()`

Iterables support Python's iterator protocol, so you can use them in `for` loops:

```python
with open_iterable('data.csv') as source:
    for row in source:
        print(row)
```

## Writing Methods

### `write(record: dict) -> None`

Write a single record to the iterable.

**Parameters:**
- `record` (dict): Dictionary representing a single record

**Example:**
```python
with open_iterable('output.jsonl', mode='w') as dest:
    dest.write({'name': 'John', 'age': 30})
```

### `write_bulk(records: list[dict]) -> None`

Write multiple records at once for better performance.

**Parameters:**
- `records` (list[dict]): List of dictionaries to write

**Example:**
```python
with open_iterable('output.jsonl', mode='w') as dest:
    batch = [
        {'id': 1, 'value': 'a'},
        {'id': 2, 'value': 'b'},
        {'id': 3, 'value': 'c'}
    ]
    dest.write_bulk(batch)
```

## Utility Methods

### `reset() -> None`

Reset the iterator to the beginning of the file. Useful for re-reading files.

**Example:**
```python
with open_iterable('data.csv') as source:
    # Read all records
    for row in source:
        print(row)
    
    # Reset and read again
    source.reset()
    for row in source:
        process(row)
```

### `close() -> None`

Close the file handle and release resources. Always call this when done with an iterable.

**Example:**
```python
source = open_iterable('data.csv')
try:
    for row in source:
        process(row)
finally:
    source.close()
```

### `totals() -> int | None`

Get the total number of records in the file. Only available for some formats and engines.

**Returns:** Integer count of records, or `None` if not available.

**Example:**
```python
with open_iterable('data.csv.gz', engine='duckdb') as source:
    total = source.totals()
    print(f"Total records: {total}")
```

### `has_totals() -> bool`

Check if the iterable supports the `totals()` method.

**Returns:** `True` if totals are available, `False` otherwise.

**Example:**
```python
with open_iterable('data.csv') as source:
    if source.has_totals():
        total = source.totals()
        print(f"Total: {total}")
```

### `has_tables() -> bool`

Check if the iterable format supports multiple tables, sheets, datasets, or other named collections.

**Returns:** `True` if the format supports table listing, `False` otherwise.

**Example:**
```python
from iterable.datatypes.xlsx import XLSXIterable

if XLSXIterable.has_tables():
    # This format supports multiple sheets
    with open_iterable('data.xlsx') as source:
        sheets = source.list_tables()
        print(f"Available sheets: {sheets}")
```

### `list_tables(filename: str | None = None) -> list[str] | None`

List available tables, sheets, datasets, layers, or other named collections in the file.

**Parameters:**
- `filename` (str | None): Optional filename. If provided, opens the file temporarily to list tables. If `None`, uses the instance's filename and reuses any open connections.

**Returns:** 
- `list[str]`: List of table/sheet names if the format supports it
- `[]`: Empty list if the file has no tables
- `None`: If the format doesn't support table listing

**Example - Discovery before opening:**
```python
from iterable.datatypes.xlsx import XLSXIterable

# List sheets without opening the file
sheets = XLSXIterable('data.xlsx').list_tables('data.xlsx')
print(f"Available sheets: {sheets}")

# Then open specific sheet
source = open_iterable('data.xlsx', iterableargs={'page': sheets[1]})
```

**Example - Discovery after opening:**
```python
# Open file on first sheet
with open_iterable('data.xlsx', iterableargs={'page': 0}) as source:
    # List all available sheets (reuses open workbook)
    all_sheets = source.list_tables()
    print(f"All sheets: {all_sheets}")
    
    # Process current sheet
    for row in source:
        process(row)
```

**Example - Database tables:**
```python
# List tables in SQLite database
source = open_iterable('data.db', iterableargs={'table': 'users'})
tables = source.list_tables()  # Reuses connection
print(f"Available tables: {tables}")

# Switch to different table
source2 = open_iterable('data.db', iterableargs={'table': tables[1]})
```

**Supported Formats:**
- **Excel formats** (XLSX, XLS, ODS): Returns sheet names
- **Database formats** (SQLite, DuckDB): Returns table names
- **Scientific formats** (HDF5, NetCDF): Returns dataset/variable names
- **Geospatial formats** (GeoPackage): Returns layer names
- **Statistical formats** (RData): Returns R object names
- **Markup formats** (HTML, XML): Returns table IDs/indices (HTML) or tag names (XML)
- **Archive formats** (ZIPXML): Returns XML filenames within ZIP archive
- **Data lake formats** (Iceberg, Hudi): Returns table names from catalogs
- **Other formats**: Returns `None` (not supported)

## Complete Example

```python
from iterable import open_iterable

# Reading
with open_iterable('input.csv') as source:
    # Method 1: Iterator protocol
    for row in source:
        print(row)
    
    # Method 2: Reset and read again
    source.reset()
    record = source.read()
    print(record)
    
    # Method 3: Bulk reading
    source.reset()
    batch = source.read_bulk(1000)
    for record in batch:
        process(record)

# Writing
with open_iterable('output.jsonl', mode='w') as dest:
    # Method 1: Single writes
    dest.write({'id': 1, 'value': 'a'})
    dest.write({'id': 2, 'value': 'b'})
    
    # Method 2: Bulk writes
    batch = [
        {'id': 3, 'value': 'c'},
        {'id': 4, 'value': 'd'}
    ]
    dest.write_bulk(batch)
finally:
    dest.close()
```

## Best Practices

1. **Always close files**: Use `close()` or try/finally blocks
2. **Use bulk operations**: `read_bulk()` and `write_bulk()` are faster for large files
3. **Check totals availability**: Use `has_totals()` before calling `totals()`
4. **Reset when needed**: Use `reset()` to re-read files
5. **Discover tables before opening**: Use `list_tables()` to explore multi-table files before processing
6. **Reuse connections**: When already opened, `list_tables()` reuses open connections for efficiency

## Related Topics

- [open_iterable()](/api/open-iterable) - Creating iterables
- [Basic Usage](/getting-started/basic-usage) - Common patterns
- [Data Pipelines](/use-cases/data-pipelines) - Processing pipelines
