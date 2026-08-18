# DuckDB Format

## Description

DuckDB is an in-process analytical database management system designed for analytical workloads. DuckDB databases are stored in single files and provide high-performance SQL queries on data. DuckDB is optimized for analytical queries and supports a wide range of data types and SQL features.

## File Extensions

- `.duckdb` - DuckDB database files
- `.ddb` - DuckDB database files (alias)

## Implementation Details

### Reading

The DuckDB implementation:
- Uses the `duckdb` Python library
- Supports reading from specific table or custom SQL query
- If no table/query specified, reads from first table in the database
- Converts rows to dictionaries
- Requires file path (not stream)
- Supports totals counting for efficient row counting

### Writing

Writing support:
- Creates tables automatically if they don't exist
- Inserts records into specified table
- Supports bulk inserts for better performance
- Columns stored as VARCHAR (flexible type handling)
- Auto-commits transactions

### Key Features

- **SQL support**: Can use custom SQL queries for reading
- **Table selection**: Can read from specific table
- **Auto-create tables**: Automatically creates tables when writing
- **Totals support**: Can count total rows efficiently
- **High performance**: Optimized for analytical queries
- **Type flexibility**: VARCHAR columns handle various data types

## Usage

```python
from iterable import open_iterable

# Recommended: Using context manager (automatic cleanup)
# Reading from first table
with open_iterable('data.duckdb') as source:
    for row in source:
        print(row)
# File automatically closed

# Reading from specific table
with open_iterable('data.duckdb', iterableargs={
    'table': 'users'
}) as source:
    for row in source:
        print(row)

# Reading with custom query
with open_iterable('data.duckdb', iterableargs={
    'query': 'SELECT * FROM users WHERE age > 18'
}) as source:
    for row in source:
        print(row)

# List available tables
from iterable.datatypes.duckdb import DuckDBDatabaseIterable

# Before opening - discover tables
tables = DuckDBDatabaseIterable('data.duckdb').list_tables('data.duckdb')
print(f"Available tables: {tables}")

# After opening - list all tables (reuses connection)
source = open_iterable('data.duckdb', iterableargs={'table': 'users'})
all_tables = source.list_tables()  # Reuses open connection
print(f"All tables: {all_tables}")

# Process each table
for table_name in all_tables:
    source = open_iterable('data.duckdb', iterableargs={'table': table_name})
    print(f"Processing table: {table_name}")
    for row in source:
        process(row)
    source.close()

# Writing
with open_iterable('output.duckdb', mode='w', iterableargs={
    'table': 'users'
}) as dest:
    dest.write({'id': 1, 'name': 'John', 'age': 30})
# File automatically closed

# Bulk writing (recommended for better performance)
with open_iterable('output.duckdb', mode='w', iterableargs={
    'table': 'users'
}) as dest:
    records = [
        {'id': 1, 'name': 'John', 'age': 30},
        {'id': 2, 'name': 'Jane', 'age': 25}
    ]
    dest.write_bulk(records)
# File automatically closed

# Alternative: Manual close (still supported)
source = open_iterable('data.duckdb')
try:
    for row in source:
        print(row)
finally:
    source.close()
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `table` | str | None | Yes* | Table name to read from or write to. Required when writing. When reading, defaults to first table if not specified. |
| `query` | str | None | No | Custom SQL query for reading. Overrides `table` parameter if provided. Only valid for reading. |

\* Required when writing, optional when reading (defaults to first table if not specified)

## Error Handling

```python
from iterable import open_iterable

try:
    # Reading with error handling
    with open_iterable('data.duckdb', iterableargs={
        'table': 'users'
    }) as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("Database file not found")
except Exception as e:
    print(f"Error reading DuckDB: {e}")

try:
    # Writing with error handling
    with open_iterable('output.duckdb', mode='w', iterableargs={
        'table': 'users'
    }) as dest:
        dest.write({'id': 1, 'name': 'John'})
except Exception as e:
    print(f"Error writing to DuckDB: {e}")
```

### Common Errors

- **"Table not found"**: Check table name spelling, or omit `table` parameter to use first table
- **"File path required"**: DuckDB requires a file path string, not a stream object
- **"No such table" when writing**: Table will be created automatically, ensure write mode is used

## Limitations

1. **File path required**: Requires filename, not stream
2. **Type storage**: All columns stored as VARCHAR (DuckDB handles type inference)
3. **Flat data only**: Only supports tabular data
4. **No schema definition**: Tables created with VARCHAR columns only
5. **Single file**: DuckDB is a single-file database
6. **DuckDB dependency**: Requires `duckdb` Python package

## Compression Support

DuckDB files can be compressed with all supported codecs:
- GZip (`.duckdb.gz`)
- BZip2 (`.duckdb.bz2`)
- LZMA (`.duckdb.xz`)
- LZ4 (`.duckdb.lz4`)
- ZIP (`.duckdb.zip`)
- Brotli (`.duckdb.br`)
- ZStandard (`.duckdb.zst`)

Note: Compressed DuckDB files cannot be used directly - they must be decompressed first.

## Use Cases

- **Analytical databases**: High-performance analytical queries
- **Data analysis**: Fast SQL queries on large datasets
- **Embedded analytics**: Embedded analytical database in applications
- **Data warehousing**: Lightweight data warehouse solutions
- **ETL pipelines**: Data transformation and loading operations

## Installation

DuckDB is an optional dependency. Install it separately:

```bash
pip install duckdb
```

## Related Formats

- [SQLite](sqlite.md) - Similar embedded database format
- [Parquet](parquet.md) - Columnar format for analytics
- [CSV](csv.md) - Simple text format
- [PostgreSQL Copy](pgcopy.md) - PostgreSQL format

## Performance Considerations

DuckDB is optimized for analytical workloads and provides excellent performance:

### Performance Tips

- **Use bulk operations**: Use `write_bulk()` instead of individual `write()` calls for better performance
  ```python
  # Recommended: Bulk write
  with open_iterable('output.duckdb', mode='w', iterableargs={'table': 'users'}) as dest:
      dest.write_bulk(records)  # Much faster than individual writes
  
  # Not recommended: Individual writes
  with open_iterable('output.duckdb', mode='w', iterableargs={'table': 'users'}) as dest:
      for record in records:
          dest.write(record)  # Slower
  ```

- **Batch size**: For large datasets, process in batches of 10,000-50,000 records
- **Use SQL queries**: For filtering and aggregations, use SQL queries instead of Python loops
- **Compression**: DuckDB files can be compressed, but compressed files must be decompressed before use

### Performance Characteristics

- **Analytical queries**: Fast aggregations and joins
- **Large datasets**: Efficient handling of large tables
- **Columnar operations**: Optimized columnar storage and queries
- **Vectorized execution**: High-performance query execution
- **Memory efficient**: Processes data efficiently without loading entire database

## Example: Data Analysis

```python
from iterable import open_iterable

# Write data to DuckDB
with open_iterable('analytics.duckdb', mode='w', iterableargs={
    'table': 'events'
}) as dest:
    dest.write_bulk([
        {'event_id': 1, 'user_id': 100, 'timestamp': '2024-01-01', 'value': 50},
        {'event_id': 2, 'user_id': 101, 'timestamp': '2024-01-02', 'value': 75},
        {'event_id': 3, 'user_id': 100, 'timestamp': '2024-01-03', 'value': 30}
    ])

# Query with aggregations
with open_iterable('analytics.duckdb', iterableargs={
    'query': 'SELECT user_id, SUM(value) as total FROM events GROUP BY user_id'
}) as source:
    for row in source:
        print(f"User {row['user_id']}: {row['total']}")
```

