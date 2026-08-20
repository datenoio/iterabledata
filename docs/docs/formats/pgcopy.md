# PostgreSQL Copy Format

## Description

PostgreSQL COPY format is a tab-delimited text format used by PostgreSQL for bulk data import/export. It's similar to CSV but uses tab delimiters and has specific handling for NULL values (represented as `\N`).

## File Extensions

- `.copy` - PostgreSQL COPY format files
- `.pgcopy` - PostgreSQL COPY format files (alias)

## Implementation Details

### Reading

The PostgreSQL Copy implementation:
- Uses tab delimiter by default
- Handles NULL values (represented as `\N`)
- Auto-detects headers (if first line doesn't contain numbers)
- Converts NULL values to Python `None`
- Converts each row to a dictionary

### Writing

Writing support:
- Writes tab-delimited format
- Converts `None` values to `\N`
- Supports custom delimiter
- Requires field names specification

### Key Features

- **Tab-delimited**: Uses tab character as delimiter
- **NULL handling**: Properly handles PostgreSQL NULL values
- **Header detection**: Automatically detects headers
- **Totals support**: Can count total rows
- **Bulk operations**: Designed for bulk data operations

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.copy') as source:
    for row in source:
        print(row)

# Writing
with open_iterable('output.copy', mode='w', iterableargs={
    'keys': ['id', 'name', 'value']
}) as dest:
    dest.write({'id': '1', 'name': 'John', 'value': None})  # None becomes \N
```

## Parameters

- `delimiter` (str): Field delimiter (default: `\t`)
- `null` (str): NULL value representation (default: `\\N`)
- `keys` (list[str]): Column names (required for writing)

## Limitations

1. **Flat data only**: Only supports tabular data
2. **Schema required for writing**: Must specify field names
3. **No type preservation**: All values are strings
4. **Tab in data**: If data contains tabs, they must be handled carefully

## Compression Support

PostgreSQL Copy files can be compressed with all supported codecs:
- GZip (`.copy.gz`)
- BZip2 (`.copy.bz2`)
- LZMA (`.copy.xz`)
- LZ4 (`.copy.lz4`)
- ZIP (`.copy.zip`)
- Brotli (`.copy.br`)
- ZStandard (`.copy.zst`)

## Use Cases

- **PostgreSQL import/export**: Bulk data operations with PostgreSQL
- **Database migration**: Moving data between databases
- **ETL pipelines**: Data transformation pipelines
- **Bulk loading**: Fast bulk data loading

## Related Formats

- [CSV](csv.md) - Comma-separated format
- [TSV](csv.md) - Tab-separated format (uses CSV)
- [SQLite](sqlite.md) - SQLite database format
