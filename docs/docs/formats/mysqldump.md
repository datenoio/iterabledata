# MySQL Dump Format

## Description

MySQL Dump format is the output format of the `mysqldump` utility. It contains SQL statements for creating tables and inserting data. The implementation parses INSERT statements and extracts data rows from the dump file.

## File Extensions

- `.sql` - SQL dump files
- `.mysqldump` - MySQL dump files (alias)

## Implementation Details

### Reading

The MySQL Dump implementation:
- Parses SQL INSERT statements
- Extracts table names and data values
- Handles multi-line INSERT statements
- Converts INSERT values to dictionaries
- Supports filtering by table name

### Writing

Writing is not currently supported for MySQL Dump format.

### Key Features

- **SQL parsing**: Parses SQL INSERT statements
- **Table extraction**: Extracts data from specific tables
- **Multi-line support**: Handles multi-line INSERT statements
- **Totals support**: Can count total rows
- **Flat data**: Extracts tabular data from INSERT statements

## Usage

```python
from iterable import open_iterable

# Basic reading (all tables)
source = open_iterable('dump.sql')
for row in source:
    print(row)  # Contains _table and column values
source.close()

# Filter by table name
source = open_iterable('dump.sql', iterableargs={
    'table_name': 'users'
})
```

## Parameters

- `table_name` (str): Optional - Filter by specific table name
- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **Read-only**: MySQL Dump format does not support writing
2. **SQL parsing**: Only parses INSERT statements
3. **Format-specific**: Must follow mysqldump format
4. **Table filtering**: Can filter by table name
5. **Value parsing**: Complex SQL values may require manual handling

## Compression Support

MySQL Dump files can be compressed with all supported codecs:
- GZip (`.sql.gz`)
- BZip2 (`.sql.bz2`)
- LZMA (`.sql.xz`)
- LZ4 (`.sql.lz4`)
- ZIP (`.sql.zip`)
- Brotli (`.sql.br`)
- ZStandard (`.sql.zst`)

## Use Cases

- **Database migration**: Migrating MySQL data
- **Backup processing**: Processing database backups
- **Data extraction**: Extracting data from SQL dumps
- **ETL pipelines**: Data transformation from SQL dumps

## Related Formats

- [PostgreSQL Copy](pgcopy.md) - PostgreSQL format
- [SQLite](sqlite.md) - SQLite database format
- [CSV](csv.md) - Simple text format
