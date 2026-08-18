---
sidebar_position: 3
title: Basic Usage
description: Common usage patterns and best practices
---

# Basic Usage

This guide covers common usage patterns and best practices for working with Iterable Data.

## Reading Compressed Files

Iterable Data seamlessly handles compressed files:

```python
from iterable import open_iterable

# Recommended: Using context manager (automatic cleanup)
# Read compressed CSV file (supports .gz, .bz2, .xz, .zst, .lz4, .br, .snappy, .lzo)
with open_iterable('data.csv.xz') as source:
    n = 0
    for row in source:
        n += 1
        # Process row data
        if n % 1000 == 0:
            print(f'Processed {n} rows')
# File automatically closed
```

## Format Detection and Encoding

IterableData automatically detects file formats using a two-stage approach: filename extension detection (primary) and content-based detection (fallback). You can also detect file types and encoding manually before opening:

```python
from iterable import open_iterable
from iterable.helpers.detect import detect_file_type
from iterable.helpers.utils import detect_encoding, detect_delimiter

# Detect file type and compression
result = detect_file_type('data.csv.gz')
print(f"Type: {result['datatype']}, Codec: {result['codec']}")

# Content-based detection (when filename detection fails)
with open('data', 'rb') as f:
    result = detect_file_type('data', fileobj=f)
    print(f"Detected format: {result['datatype']}")

# Detect encoding for CSV files
encoding_info = detect_encoding('data.csv')
print(f"Encoding: {encoding_info['encoding']}, Confidence: {encoding_info['confidence']}")

# Detect delimiter for CSV files
delimiter = detect_delimiter('data.csv', encoding=encoding_info['encoding'])

# Open with detected settings
with open_iterable('data.csv', iterableargs={
    'encoding': encoding_info['encoding'],
    'delimiter': delimiter
}) as source:
    for row in source:
        print(row)
```

### Content-Based Detection

When files don't have extensions or have unknown extensions, the library automatically uses content-based detection:

**Binary formats** are detected by magic numbers:
- Parquet: `PAR1` header
- ORC: `ORC` header
- PCAP: `\xa1\xb2\xc3\xd4` or `\xd4\xc3\xb2\xa1` header
- Arrow: `ARROW1` header
- ZIP/XLSX: `PK\x03\x04` header

**Text formats** are detected by heuristics:
- JSON: Valid JSON structure (`{...}` or `[...]`)
- JSONL: Multiple lines of valid JSON
- CSV/TSV: Consistent delimiter patterns across lines

**Example:**
```python
# File without extension - automatically detected from content
with open_iterable('data') as source:  # Contains JSON content
    for row in source:
        print(row)  # Automatically detected as JSON
```

See [Format Detection Details](/api/open-iterable#format-detection-details) for complete information.

## Working with Excel Files

Excel files can be read with sheet selection:

```python
from iterable import open_iterable

# Recommended: Using context manager
# Read Excel file (specify sheet or page)
with open_iterable('data.xlsx', iterableargs={'page': 0}) as xls_file:
    for row in xls_file:
        print(row)
# File automatically closed

# Read specific sheet in XLSX
with open_iterable('data.xlsx', iterableargs={'page': 'Sheet2'}) as xlsx_file:
    for row in xlsx_file:
        print(row)
```

## XML Processing

XML files require specifying the tag name to iterate over:

```python
from iterable import open_iterable

# Recommended: Using context manager
# Parse XML with specific tag name
with open_iterable(
    'data.xml',
    iterableargs={
        'tagname': 'book',
        'prefix_strip': True  # Strip XML namespace prefixes
    }
) as xml_file:
    for item in xml_file:
        print(item)
# File automatically closed
```

## Bulk Operations

For better performance with large files, use bulk operations:

```python
from iterable import open_iterable

# Recommended: Using context managers
with open_iterable('input.jsonl') as source:
    with open_iterable('output.parquet', mode='w') as destination:
        # Read and write in batches for better performance
        batch = []
        for row in source:
            batch.append(row)
            if len(batch) >= 10000:
                destination.write_bulk(batch)
                batch = []
        
        # Write remaining records
        if batch:
            destination.write_bulk(batch)
# Files automatically closed
```

## Using Context Managers

Iterable Data supports Python's context manager protocol (`with` statements) for automatic resource cleanup:

```python
from iterable import open_iterable

# Recommended: Using context manager (automatic cleanup)
with open_iterable('data.csv') as source:
    for row in source:
        process(row)
# File automatically closed when exiting the block

# Alternative: Manual close (still supported)
source = open_iterable('data.csv')
try:
    for row in source:
        process(row)
finally:
    source.close()
```

## Error Handling

Always handle potential errors when working with files:

```python
from iterable import open_iterable

# Recommended: Using context manager with error handling
try:
    with open_iterable('data.csv') as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("File not found")
except UnicodeDecodeError:
    print("Encoding error - try specifying encoding explicitly")
    # Retry with explicit encoding
    with open_iterable('data.csv', iterableargs={'encoding': 'latin-1'}) as source:
        for row in source:
            process(row)
except Exception as e:
    print(f"Error processing file: {e}")
```

## Querying Format Capabilities

Before working with a format, you can programmatically check what capabilities it supports:

```python
from iterable.helpers.capabilities import (
    get_format_capabilities,
    get_capability,
    list_all_capabilities
)

# Check if a format supports writing before attempting to write
if get_capability("csv", "writable"):
    with open_iterable("output.csv", mode="w") as dest:
        dest.write({"name": "Alice", "age": 30})

# Check if format supports totals for progress tracking
if get_capability("parquet", "totals"):
    with open_iterable("data.parquet") as source:
        total = source.totals()
        print(f"Processing {total} rows...")

# Find formats that support multiple tables
all_caps = list_all_capabilities()
multi_table_formats = [
    fmt_id for fmt_id, caps in all_caps.items()
    if caps.get("tables")
]
print(f"Formats with table support: {multi_table_formats}")
```

**Use Cases:**
- **Format Selection**: Choose the best format based on required capabilities
- **Adaptive Code**: Write code that adapts to format capabilities
- **Error Prevention**: Check capabilities before attempting operations
- **Documentation**: Generate capability reports or format comparison tables

See the [Capability Matrix](/api/capabilities) documentation for complete details.

## Type Hints and Type Safety

IterableData provides comprehensive type hints for better IDE support and static type checking. You can also use typed helper functions for type-safe data processing.

### Using Type Hints

Type hints improve IDE autocomplete and enable static type checking with tools like mypy or pyright:

```python
from iterable import open_iterable, Row, IterableArgs

# Type hints help IDEs understand return types
def process_csv(filename: str) -> list[Row]:
    rows: list[Row] = []
    with open_iterable(filename) as source:
        row: Row = source.read()
        rows.append(row)
        # Process more rows...
    return rows

# Type hints for configuration arguments
config: IterableArgs = {
    'delimiter': ',',
    'encoding': 'utf-8'
}
with open_iterable('data.csv', iterableargs=config) as source:
    for row in source:
        process(row)
```

### Typed Helpers: Dataclasses

Convert dict-based rows into dataclass instances for type-safe data processing:

```python
from dataclasses import dataclass
from iterable import open_iterable, as_dataclasses

@dataclass
class Person:
    name: str
    age: int
    email: str

# Convert rows to dataclass instances
with open_iterable('people.csv') as source:
    for person in as_dataclasses(source, Person):
        # Type checkers recognize person as Person type
        print(f"{person.name} is {person.age} years old")
        # IDE autocomplete works for person.name, person.age, etc.
```

**Benefits:**
- **Type safety**: Catch errors at development time
- **IDE support**: Better autocomplete and type checking
- **Cleaner code**: Access fields as attributes instead of dict keys

### Typed Helpers: Pydantic Models

For more advanced validation, use Pydantic models:

```python
from pydantic import BaseModel
from iterable import open_iterable, as_pydantic

class PersonModel(BaseModel):
    name: str
    age: int
    email: str

# Convert rows to Pydantic model instances with validation
with open_iterable('people.csv') as source:
    for person in as_pydantic(source, PersonModel, validate=True):
        # Rows are validated against the model schema
        # Invalid rows raise ValidationError
        print(f"{person.name} ({person.email})")
```

**Installation:**
```bash
pip install iterabledata[pydantic]
```

**Benefits:**
- **Automatic validation**: Catches schema mismatches early
- **Type conversion**: Automatically converts types (e.g., string to int)
- **Rich error messages**: Detailed validation errors for debugging

See the [Type System](/api/type-system) documentation for complete details.

## Best Practices

1. **Use context managers**: Prefer `with` statements for automatic resource cleanup
2. **Use bulk operations**: For large files, use `write_bulk()` and `read_bulk()` for better performance
3. **Handle encoding**: For text files, let the library auto-detect encoding or specify it explicitly
4. **Use compression**: Compressed files save space and often process faster
5. **Check format support**: Verify that your format supports read/write operations before use using capability queries
6. **Handle errors**: Always wrap file operations in try/except blocks for production code
7. **Batch processing**: Process large files in batches (10,000-50,000 records) for optimal performance

## Next Steps

- [Use Cases](/use-cases/format-conversion) - See real-world examples
- [API Reference](/api/open-iterable) - Explore the full API
- [Supported Formats](/formats/) - Learn about specific formats
