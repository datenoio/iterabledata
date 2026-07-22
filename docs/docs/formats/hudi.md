# Apache Hudi Format

## Description

Apache Hudi (Hadoop Upserts Deletes and Incrementals) is a data lake platform that brings stream processing to data lakes. It provides upserts, deletes, and incremental processing capabilities on top of data stored in cloud storage.

## File Extensions

- No specific extension (Hudi tables are directories)

## Implementation Details

### Reading

The Hudi implementation:
- Uses `pyhudi` or `hudi` library for reading
- Requires `table_path` parameter (path to Hudi table)
- Loads table and converts to pandas DataFrame, then to dictionaries
- Requires table path (not stream)

### Writing

Writes are **deferred**: opening a Hudi iterable in write mode raises `WriteNotSupportedError`. Read-only access remains available when `pyhudi` / `hudi` is installed.

### Key Features

- **Upserts**: Update and insert operations
- **Deletes**: Delete operations
- **Incremental processing**: Process only changed data
- **Totals support**: Can count total rows
- **Data lake**: Designed for data lake architectures

## Usage

```python
from iterable.helpers.detect import open_iterable

# Reading Hudi table
source = open_iterable('/path/to/hudi/table', iterableargs={
    'table_path': '/path/to/hudi/table'
})
for row in source:
    print(row)
source.close()

# Discover available tables in catalog/directory
from iterable.datatypes.hudi import HudiIterable

# Before opening - discover tables (if catalog-based)
iterable = HudiIterable(filename='/path/to/catalog', table_path='/path/to/catalog')
tables = iterable.list_tables('/path/to/catalog')
if tables:
    print(f"Available tables: {tables}")
else:
    print("Single table path or catalog doesn't support listing")

# After opening - list all tables (reuses catalog connection)
source = open_iterable('/path/to/hudi/table', iterableargs={
    'table_path': '/path/to/hudi/table'
})
all_tables = source.list_tables()  # May return None for single table paths
if all_tables:
    print(f"All tables: {all_tables}")

# Process different tables (if catalog-based)
if all_tables:
    for table_name in all_tables:
        source = open_iterable('/path/to/catalog', iterableargs={
            'table_path': f'/path/to/catalog/{table_name}'
        })
        print(f"Processing table: {table_name}")
        for row in source:
            process(row)
        source.close()
```

### Discovering Available Tables

Hudi catalogs or directories can contain multiple tables. Use `list_tables()` to discover available tables:

```python
from iterable.datatypes.hudi import HudiIterable

# Before opening - discover tables (if catalog-based)
iterable = HudiIterable(filename='/path/to/catalog', table_path='/path/to/catalog')
tables = iterable.list_tables('/path/to/catalog')
if tables:
    print(f"Available tables: {tables}")
    # Output: ['events', 'users', 'transactions']
else:
    print("Single table path or catalog doesn't support listing")

# Note: list_tables() returns None for single table paths
# It only returns a list when the path is a catalog with multiple tables
```

## Parameters

- `table_path` (str): **Required** - Path to the Hudi table directory

## Limitations

1. **Read-only**: Hudi format does not support writing
2. **Dependency**: Requires `pyhudi` or `hudi` package
3. **Table path required**: Requires path to table directory
4. **Flat data only**: Only supports tabular data
5. **Memory usage**: Entire table may be loaded into memory

## Compression Support

Hudi uses underlying file formats (typically Parquet) which have built-in compression. Hudi tables themselves are directories.

## Use Cases

- **Data lakes**: Managing data in data lakes
- **Upserts**: When you need update/insert operations
- **Streaming**: Real-time data processing
- **Incremental processing**: Processing only changed data

## Related Formats

- [Parquet](parquet.md) - Common underlying format
- [Delta Lake](delta.md) - Similar data lake format
- [Iceberg](iceberg.md) - Another table format
