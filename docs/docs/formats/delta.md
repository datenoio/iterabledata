# Delta Lake Format

## Description

Delta Lake is an open-source storage layer that brings ACID transactions to Apache Spark and big data workloads. It provides data versioning, time travel, and schema evolution capabilities on top of Parquet files.

## File Extensions

- No specific extension (Delta tables are directories)

## Implementation Details

### Reading

The Delta Lake implementation:
- Uses `deltalake` library for reading
- Requires path to Delta table directory (not a file)
- Converts Delta table to PyArrow table
- Iterates over records as dictionaries
- Requires file path (not stream)

### Writing

Writes use `deltalake.write_deltalake` with `write_mode` of `append` (default), `overwrite`, or `error`:

```python
with open_iterable("/path/to/delta/table", mode="w", iterableargs={
    "format": "delta",
    "write_mode": "overwrite",
}) as dest:
    dest.write_bulk([{"id": 1, "name": "Alice"}])
```

### Key Features

- **ACID transactions**: Transactional guarantees
- **Time travel**: Access historical versions of data
- **Schema evolution**: Handles schema changes
- **Totals support**: Can count total rows
- **Parquet-based**: Built on Parquet format

## Usage

```python
from iterable import open_iterable

# Reading Delta table (path to table directory)
source = open_iterable('/path/to/delta/table')
for row in source:
    print(row)
source.close()

# Note: Delta Lake typically uses single table directories
# list_tables() returns None for single table directories
# Catalog-based listing would require additional configuration

from iterable.datatypes.delta import DeltaIterable

# Check if format supports table listing
if DeltaIterable.has_tables():
    # For catalog-based Delta Lake (requires additional setup)
    iterable = DeltaIterable('/path/to/catalog')
    tables = iterable.list_tables('/path/to/catalog')
    if tables:
        print(f"Available tables: {tables}")
else:
    # Most Delta Lake usage is single table directories
    print("Delta Lake table listing not available for single table directories")
```

### Table Listing

Delta Lake typically works with single table directories (each directory is one table). The `list_tables()` method returns `None` for single table directories, which is the most common usage pattern.

For catalog-based Delta Lake (Unity Catalog, Hive Metastore), table listing would require additional catalog configuration. Currently, `has_tables()` returns `False` and `list_tables()` returns `None` to indicate that table listing is not applicable for single-table directories.

```python
from iterable.datatypes.delta import DeltaIterable

# Check if format supports table listing
assert DeltaIterable.has_tables() is False  # Single table directories

# list_tables() returns None for single table directories
iterable = DeltaIterable('/path/to/delta/table')
tables = iterable.list_tables()
assert tables is None  # Single table directory, listing not applicable
```

## Parameters

No specific parameters required. The filename should be the path to the Delta table directory.

## Limitations

1. **deltalake dependency**: Requires `deltalake` package
2. **Directory path required**: Requires path to table directory, not a file
3. **Flat data only**: Only supports tabular data
4. **Memory usage**: Entire table may be loaded into memory on read
5. **Write modes**: Use `write_mode` of `append` (default), `overwrite`, or `error` via `iterableargs`

## Compression Support

Delta Lake uses Parquet files internally, which have built-in compression. Delta tables themselves are directories, so file-level compression doesn't apply directly.

## Use Cases

- **Data lakes**: Managing data in data lakes
- **ETL pipelines**: Transactional data processing
- **Data versioning**: When you need data versioning
- **Schema evolution**: When schemas change over time

## Related Formats

- [Parquet](parquet.md) - Base format used by Delta Lake
- [Iceberg](iceberg.md) - Similar table format
- [Hudi](hudi.md) - Another data lake format
