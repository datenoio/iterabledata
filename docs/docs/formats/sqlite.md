# SQLite Format

## Description

SQLite is a self-contained, serverless, zero-configuration, transactional SQL database engine. SQLite databases are stored in single files and are widely used for embedded databases, mobile applications, and small to medium-sized applications.

## File Extensions

- `.sqlite` - SQLite database files
- `.db` - SQLite database files (alias)

## Implementation Details

### Reading

The SQLite implementation:
- Uses Python's built-in `sqlite3` module
- Supports reading from specific table or custom SQL query
- If no table/query specified, reads from first table
- Converts rows to dictionaries
- Requires file path (not stream)

### Writing

Writing support:
- Creates tables automatically if they don't exist
- Inserts records into specified table
- Supports bulk inserts
- All columns stored as TEXT (type conversion handled by SQLite)

### Key Features

- **SQL support**: Can use custom SQL queries
- **Table selection**: Can read from specific table
- **Auto-create tables**: Automatically creates tables when writing
- **Totals support**: Can count total rows
- **Transaction support**: Uses SQLite transactions

## Usage

```python
from iterable import open_iterable

# Recommended: Using context manager (automatic cleanup)
# Reading from first table
with open_iterable('data.db') as source:
    for row in source:
        print(row)
# File automatically closed

# Reading from specific table
with open_iterable('data.db', iterableargs={
    'table': 'users'
}) as source:
    for row in source:
        print(row)

# Reading with custom query
with open_iterable('data.db', iterableargs={
    'query': 'SELECT * FROM users WHERE age > 18'
}) as source:
    for row in source:
        print(row)

# List available tables
from iterable.datatypes.sqlite import SQLiteIterable

# Before opening - discover tables
tables = SQLiteIterable('data.db').list_tables('data.db')
print(f"Available tables: {tables}")

# After opening - list all tables (reuses connection)
source = open_iterable('data.db', iterableargs={'table': 'users'})
all_tables = source.list_tables()  # Reuses open connection
print(f"All tables: {all_tables}")

# Process each table
for table_name in all_tables:
    source = open_iterable('data.db', iterableargs={'table': table_name})
    print(f"Processing table: {table_name}")
    for row in source:
        process(row)
    source.close()

# Writing
with open_iterable('output.db', mode='w', iterableargs={
    'table': 'users'
}) as dest:
    dest.write({'id': 1, 'name': 'John', 'age': 30})
# File automatically closed

# Bulk writing (recommended for better performance)
with open_iterable('output.db', mode='w', iterableargs={
    'table': 'users'
}) as dest:
    records = [
        {'id': 1, 'name': 'John', 'age': 30},
        {'id': 2, 'name': 'Jane', 'age': 25}
    ]
    dest.write_bulk(records)
# File automatically closed

# Alternative: Manual close (still supported)
source = open_iterable('data.db')
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
    with open_iterable('data.db', iterableargs={
        'table': 'users'
    }) as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("Database file not found")
except Exception as e:
    print(f"Error reading SQLite: {e}")

try:
    # Writing with error handling
    with open_iterable('output.db', mode='w', iterableargs={
        'table': 'users'
    }) as dest:
        dest.write({'id': 1, 'name': 'John'})
except Exception as e:
    print(f"Error writing to SQLite: {e}")
```

### Common Errors

- **"Table not found"**: Check table name spelling, or omit `table` parameter to use first table
- **"File path required"**: SQLite requires a file path string, not a stream object
- **"No such table" when writing**: Table will be created automatically, ensure write mode is used

## Limitations

1. **File path required**: Requires filename, not stream
2. **Type storage**: All columns stored as TEXT (SQLite handles conversion)
3. **Flat data only**: Only supports tabular data
4. **No schema definition**: Tables created with TEXT columns only
5. **Single file**: SQLite is a single-file database

## Compression Support

SQLite files can be compressed with all supported codecs:
- GZip (`.db.gz`)
- BZip2 (`.db.bz2`)
- LZMA (`.db.xz`)
- LZ4 (`.db.lz4`)
- ZIP (`.db.zip`)
- Brotli (`.db.br`)
- ZStandard (`.db.zst`)

Note: Compressed SQLite files cannot be used directly - they must be decompressed first.

## Performance Considerations

### Performance Tips

- **Use bulk operations**: Use `write_bulk()` instead of individual `write()` calls for better performance
  ```python
  # Recommended: Bulk write
  with open_iterable('output.db', mode='w', iterableargs={'table': 'users'}) as dest:
      dest.write_bulk(records)  # Much faster than individual writes
  ```

- **Batch size**: For large datasets, process in batches of 10,000-50,000 records
- **Use SQL queries**: For filtering and aggregations, use SQL queries instead of Python loops
- **Transactions**: SQLite uses transactions automatically, which improves write performance
- **Compression**: SQLite files can be compressed, but compressed files must be decompressed before use

## Use Cases

- **Embedded databases**: Applications with embedded databases
- **Mobile apps**: Mobile application data storage
- **Small applications**: Small to medium-sized applications
- **Data analysis**: Quick data analysis with SQL

## Related Formats

- [CSV](csv.md) - Simple text format
- [Parquet](parquet.md) - Columnar format
- [PostgreSQL Copy](pgcopy.md) - PostgreSQL format
