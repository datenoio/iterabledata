---
title: CSV Format
description: CSV (Comma-Separated Values) format support in Iterable Data
---

# CSV Format

## Description

CSV (Comma-Separated Values) is a simple text format for storing tabular data. Each line represents a row, and values are separated by a delimiter (typically a comma). CSV is one of the most widely used data interchange formats.

## File Extensions

- `.csv` - Standard CSV files
- `.tsv` - Tab-separated values (handled by the CSV iterable with a tab delimiter by default, also when compressed, e.g. `.tsv.gz`)

## Implementation Details

### Reading

The CSV implementation reads with Python's `csv` module and returns the same records as
`csv.DictReader`:
- Detects encoding using `chardet` library
- Supports automatic delimiter detection
- Handles quoted fields and escaped characters
- Converts each row to a dictionary with column names as keys
- Short rows get `None` for the missing fields; extra values of long rows go to a list under the
  `None` key; blank lines are skipped

### Writing

Writing follows `csv.DictWriter`:
- Takes field names from `keys` or the first record
- Supports custom delimiters and quote characters
- Automatically handles special characters and escaping
- Writes `""` for missing fields and raises `ValueError` for fields that are not in the header

### Native batches

With PyArrow installed, `convert(..., use_native_batch=True)` streams CSV into Parquet or Arrow
IPC as Arrow record batches without building Python rows (plain, `.gz`, `.bz2` and `.zst`
files). Every column is read as a string, so values equal the row path's and empty fields stay
`""`. Column projection (`selection={"columns": [...]}`) is pushed down; predicates and row
ranges use the row path. Every row must have as many fields as the header; read ragged files
without `use_native_batch`.

### Key Features

- **Automatic encoding detection**: Uses `chardet` to detect file encoding
- **Delimiter detection**: Can automatically detect comma, semicolon, tab, or pipe delimiters
- **Customizable delimiters**: Supports any delimiter character
- **Quote handling**: Properly handles quoted fields containing delimiters
- **Totals support**: Can count total rows in file

## Usage

```python
from iterable import open_iterable

# Recommended: Using context manager (automatic cleanup)
# Basic usage with automatic detection
with open_iterable('data.csv') as source:
    for row in source:
        print(row)
# File automatically closed

# With custom delimiter and encoding
with open_iterable('data.csv', iterableargs={
    'delimiter': ';',
    'encoding': 'utf-8'
}) as source:
    for row in source:
        print(row)

# With automatic delimiter detection
with open_iterable('data.csv', iterableargs={
    'autodetect': True
}) as source:
    for row in source:
        print(row)

# Writing CSV files
with open_iterable('output.csv', mode='w', iterableargs={
    'keys': ['name', 'age', 'city']  # Required for writing
}) as dest:
    dest.write({'name': 'John', 'age': 30, 'city': 'NYC'})
    dest.write({'name': 'Jane', 'age': 25, 'city': 'LA'})

# Bulk writing (recommended for better performance)
with open_iterable('output.csv', mode='w', iterableargs={
    'keys': ['name', 'age', 'city']
}) as dest:
    records = [
        {'name': 'John', 'age': 30, 'city': 'NYC'},
        {'name': 'Jane', 'age': 25, 'city': 'LA'}
    ]
    dest.write_bulk(records)

# Alternative: Manual close (still supported)
source = open_iterable('data.csv')
try:
    for row in source:
        print(row)
finally:
    source.close()
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `delimiter` | str | `,` | No | Field delimiter character. Common values: `,` (comma), `;` (semicolon), `\t` (tab), `\|` (pipe) |
| `quotechar` | str | `"` | No | Quote character for fields containing delimiters |
| `escapechar` | str | None | No | Escape character used when `doublequote` is `False` or quoting is impossible |
| `doublequote` | bool | `True` | No | Escape a quote character inside a field by doubling it |
| `encoding` | str | auto-detected | No | File encoding. If not specified, uses `chardet` to auto-detect. Common values: `utf-8`, `latin-1`, `cp1252` |
| `keys` | list | None | Yes* | Column names. Required when writing or when reading files without headers. When reading with headers, column names are auto-detected from first row. |
| `autodetect` | bool | `False` | No | Automatically detect delimiter by analyzing first few lines of file |

\* Required when writing, optional when reading (auto-detected from headers if present)

All of these can be passed through `open_iterable(..., iterableargs={...})` or
`convert(..., iterableargs=..., toiterableargs=...)`. Precedence: an explicit constructor argument,
then `iterableargs`, then the extension default (tab for `.tsv`), then `autodetect`.

`totals()` returns the number of data rows counted by lines; the header line is not counted.
Quoted fields that contain line breaks make it an over-estimate.

## Error Handling

```python
from iterable import open_iterable

try:
    # Reading with error handling
    with open_iterable('data.csv', iterableargs={
        'encoding': 'utf-8'
    }) as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("CSV file not found")
except UnicodeDecodeError:
    print("Encoding error - try specifying encoding explicitly")
    # Retry with different encoding
    with open_iterable('data.csv', iterableargs={
        'encoding': 'latin-1'
    }) as source:
        for row in source:
            process(row)
except Exception as e:
    print(f"Error reading CSV: {e}")

try:
    # Writing with error handling
    with open_iterable('output.csv', mode='w', iterableargs={
        'keys': ['name', 'age']
    }) as dest:
        dest.write({'name': 'John', 'age': 30})
except KeyError as e:
    print(f"Missing required field: {e}")
except Exception as e:
    print(f"Error writing CSV: {e}")
```

### Common Errors

- **"No columns specified" when writing**: Provide `keys` parameter with column names
- **Encoding errors**: Specify encoding explicitly if auto-detection fails
- **Delimiter issues**: Use `autodetect=True` or specify correct delimiter
- **Missing headers**: Provide `keys` parameter when reading files without headers

## Limitations

1. **No nested data**: CSV only supports flat, tabular data structures
2. **Schema required for writing**: Must specify field names when writing
3. **No type preservation**: All values are read as strings
4. **Memory for large files**: Entire file is not loaded into memory, but encoding detection reads first 1MB
5. **No support for multi-line fields**: Standard CSV readers may have issues with fields containing newlines

## Compression Support

CSV files can be compressed with all supported codecs:
- GZip (`.csv.gz`)
- BZip2 (`.csv.bz2`)
- LZMA (`.csv.xz`)
- LZ4 (`.csv.lz4`)
- ZIP (`.csv.zip`)
- Brotli (`.csv.br`)
- ZStandard (`.csv.zst`)

## Performance Considerations

### Performance Tips

- **Use bulk operations**: Use `write_bulk()` instead of individual `write()` calls
  ```python
  # Recommended: Bulk write
  with open_iterable('output.csv', mode='w', iterableargs={'keys': ['name', 'age']}) as dest:
      dest.write_bulk(records)  # Much faster than individual writes
  ```

- **Batch processing**: For large files, process in batches of 10,000-50,000 records
- **CSV to Parquet**: `convert("a.csv", "a.parquet", use_native_batch=True)` uses the native Arrow path above
- **Compression**: Compressed CSV files (`.csv.gz`, `.csv.zst`) can be processed efficiently
- **Encoding detection**: Auto-detection reads first 1MB - specify encoding explicitly for faster startup
- **Delimiter detection**: Auto-detection has overhead - specify delimiter if known

### DuckDB Engine Support

CSV files are supported by the DuckDB engine for high-performance querying:
- Supports compressed CSV (`.gz`, `.zst`)
- Fast row counting and filtering
- SQL-like operations
- Recommended for large CSV files and analytical queries

```python
# Use DuckDB engine for better performance on large CSV files
with open_iterable('large_data.csv.gz', engine='duckdb') as source:
    total = source.totals()  # Fast row counting
    for row in source:
        process(row)
```
