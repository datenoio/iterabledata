# JSON Format

## Description

JSON (JavaScript Object Notation) is a lightweight data interchange format. It supports nested data structures including objects, arrays, strings, numbers, booleans, and null values. The JSON format in Iterable Data expects an array of objects at the root level.

## File Extensions

- `.json` - Standard JSON files

## Implementation Details

### Reading

The JSON implementation:
- Loads the entire JSON file into memory
- Expects the root element to be an array of objects
- Supports optional `tagname` parameter to extract a specific key from the root object
- Iterates over array elements, returning each as a dictionary

### Writing

Writing is not directly supported for JSON format. Use JSONL format for writing individual records.

### Key Features

- **Nested data support**: Preserves complex nested structures
- **Totals support**: Can count total records in the array
- **Tag extraction**: Can extract a specific key from root object before iterating

## Usage

```python
from iterable.helpers.detect import open_iterable

# Basic usage - expects array of objects
source = open_iterable('data.json')
for row in source:
    print(row)
source.close()

# Extract specific key from root object
source = open_iterable('data.json', iterableargs={
    'tagname': 'items'  # Extract 'items' array from root
})
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `tagname` | str | `None` | No | Key name to extract from root object before iterating. If root is an object (not array), use this to specify which key contains the array to iterate over. |

## Error Handling

```python
from iterable.helpers.detect import open_iterable
import json

try:
    # Reading with error handling
    with open_iterable('data.json', iterableargs={
        'tagname': 'items'  # Optional: extract specific key
    }) as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("JSON file not found")
except json.JSONDecodeError as e:
    print(f"Invalid JSON: {e}")
    print(f"Position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
except ValueError as e:
    # May occur if root is not an array or tagname not found
    print(f"JSON structure error: {e}")
    # Try without tagname if root is an array
    with open_iterable('data.json') as source:
        for row in source:
            process(row)
except ImportError:
    # For large files, ijson is required
    print("For large JSON files, install ijson: pip install ijson")
except Exception as e:
    print(f"Error reading JSON: {e}")
```

### Common Errors

- **JSONDecodeError**: Invalid JSON syntax - check file format and encoding
- **ValueError**: Root element is not an array, or `tagname` key not found in root object
- **ImportError**: For large files (>10MB), `ijson` package is required for streaming
- **FileNotFoundError**: File path is incorrect or file doesn't exist
- **MemoryError**: For very large files, consider using JSONL format instead

## Limitations

1. **Read-only**: JSON format does not support writing (use JSONL for writing)
2. **⚠️ Memory usage**: 
   - **Small files (under 10MB)**: Entire JSON document is loaded into memory
   - **Large files (>10MB)**: Automatically uses streaming parser (`ijson`) to avoid loading entire file
   - For very large files, prefer **JSONL** format for true line-by-line streaming
3. **Array requirement**: Root element must be an array of objects (or object with array values via `tagname`)
4. **Single document**: Only supports single JSON document per file

## Compression Support

JSON files can be compressed with all supported codecs:
- GZip (`.json.gz`)
- BZip2 (`.json.bz2`)
- LZMA (`.json.xz`)
- LZ4 (`.json.lz4`)
- ZIP (`.json.zip`)
- Brotli (`.json.br`)
- ZStandard (`.json.zst`)

## DuckDB Engine Support

JSON files are supported by the DuckDB engine:
- Supports compressed JSON (`.gz`, `.zst`)
- Fast querying and filtering
- SQL-like operations

## Related Formats

- [JSONL](jsonl.md) - For writing and streaming JSON records
- [GeoJSON](geojson.md) - For geographic data
