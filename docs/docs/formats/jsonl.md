---
title: JSONL Format (JSON Lines)
description: JSON Lines format support in Iterable Data
---

# JSONL Format (JSON Lines)

## Description

JSONL (JSON Lines) or NDJSON (Newline-Delimited JSON) is a format where each line is a valid JSON object. This format is ideal for streaming large datasets and is commonly used in data processing pipelines. Unlike standard JSON, JSONL files don't need to be loaded entirely into memory.

## File Extensions

- `.jsonl` - JSON Lines format
- `.ndjson` - Newline-Delimited JSON (alias)

## Implementation Details

### Reading

The JSONL implementation:
- Reads file line by line
- Parses each line as a separate JSON object
- Supports streaming for large files
- Handles datetime objects in JSON

### Writing

Writing support:
- Writes each record as a single line
- Automatically serializes datetime objects to ISO format
- Supports Unicode characters
- Efficient for bulk writes

### Key Features

- **Streaming support**: Processes files line by line without loading entire file
- **Memory efficient**: Suitable for very large files
- **Nested data support**: Preserves complex nested structures
- **Totals support**: Can count total lines in file
- **Datetime handling**: Automatically converts datetime objects to ISO format

## Usage

```python
from iterable import open_iterable

# Recommended: Using context manager (automatic cleanup)
# Basic usage
with open_iterable('data.jsonl') as source:
    for row in source:
        print(row)
# File automatically closed

# Writing data
with open_iterable('output.jsonl', mode='w') as dest:
    dest.write({'name': 'John', 'age': 30})
    dest.write({'name': 'Jane', 'age': 25})
# File automatically closed

# Bulk writing (recommended for better performance)
with open_iterable('output.jsonl', mode='w') as dest:
    records = [
        {'id': 1, 'value': 'a'},
        {'id': 2, 'value': 'b'}
    ]
    dest.write_bulk(records)
# File automatically closed

# With custom encoding
with open_iterable('data.jsonl', iterableargs={
    'encoding': 'utf-8'
}) as source:
    for row in source:
        print(row)

# Alternative: Manual close (still supported)
source = open_iterable('data.jsonl')
try:
    for row in source:
        print(row)
finally:
    source.close()
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `encoding` | str | `utf8` | No | File encoding for reading/writing JSONL files. UTF-8 is the standard for JSON/JSONL files. Other encodings like `latin-1` or `cp1252` are supported but not recommended. |

## Error Handling

```python
from iterable import open_iterable
import json

try:
    # Reading with error handling
    with open_iterable('data.jsonl') as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("JSONL file not found")
except json.JSONDecodeError as e:
    print(f"Invalid JSON on line: {e}")
    print(f"Line number: {e.lineno if hasattr(e, 'lineno') else 'unknown'}")
except UnicodeDecodeError:
    print("Encoding error - try specifying encoding explicitly")
    with open_iterable('data.jsonl', iterableargs={'encoding': 'latin-1'}) as source:
        for row in source:
            process(row)
except Exception as e:
    print(f"Error reading JSONL: {e}")

try:
    # Writing with error handling
    with open_iterable('output.jsonl', mode='w') as dest:
        dest.write({'name': 'John', 'age': 30})
except Exception as e:
    print(f"Error writing JSONL: {e}")
```

### Common Errors

- **JSONDecodeError**: Invalid JSON on a line - check line format and encoding
- **UnicodeDecodeError**: Encoding issue - specify correct encoding
- **FileNotFoundError**: File path is incorrect or file doesn't exist

## Limitations

1. **Line-based format**: Each record must fit on a single line
2. **No pretty printing**: Output is compact (single line per record)
3. **No validation**: Invalid JSON on a line will cause parsing errors
4. **No schema**: Each line can have different structure

## Compression Support

JSONL files can be compressed with all supported codecs:
- GZip (`.jsonl.gz`)
- BZip2 (`.jsonl.bz2`)
- LZMA (`.jsonl.xz`)
- LZ4 (`.jsonl.lz4`)
- ZIP (`.jsonl.zip`)
- Brotli (`.jsonl.br`)
- ZStandard (`.jsonl.zst`)

## Performance Considerations

### Performance Tips

- **Use bulk operations**: Use `write_bulk()` instead of individual `write()` calls for significantly better performance
  ```python
  # Recommended: Bulk write
  with open_iterable('output.jsonl', mode='w') as dest:
      dest.write_bulk(records)  # Much faster than individual writes
  
  # Not recommended: Individual writes
  with open_iterable('output.jsonl', mode='w') as dest:
      for record in records:
          dest.write(record)  # Slower
  ```

- **Batch processing**: For large files, process in batches of 10,000-50,000 records
- **Compression**: Compressed JSONL files (`.jsonl.gz`, `.jsonl.zst`) are efficient and recommended for large datasets
- **Streaming**: JSONL is processed line-by-line, making it memory-efficient for very large files
- **DuckDB engine**: Use DuckDB engine for analytical queries on large JSONL files

### DuckDB Engine Support

JSONL files are fully supported by the DuckDB engine:
- Supports compressed JSONL (`.gz`, `.zst`)
- Fast querying and filtering
- SQL-like operations
- Recommended format for large datasets with DuckDB

```python
# Use DuckDB engine for better performance on large JSONL files
with open_iterable('large_data.jsonl.gz', engine='duckdb') as source:
    total = source.totals()  # Fast row counting
    for row in source:
        process(row)
```

## Use Cases

- **Log processing**: Each log entry as a JSON line
- **Data pipelines**: Streaming data between systems
- **ETL operations**: Efficient data transformation
- **Large datasets**: When memory is a concern

## Related Formats

- [JSON](json.md) - For reading array-based JSON files
- [GeoJSON](geojson.md) - For geographic data
