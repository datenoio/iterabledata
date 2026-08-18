# Vortex Format

## Description

Vortex is a modern columnar data format designed for efficient querying and compression. It provides fast random access compared to Parquet, supports selective row reading, and offers excellent compression ratios. Vortex files use a binary format with FlatBuffer metadata, enabling efficient access patterns for both local disk and cloud storage.

## File Extensions

- `.vortex` - Vortex columnar files
- `.vtx` - Alternative extension for Vortex files

## Implementation Details

### Reading

The Vortex implementation:
- Uses `vortex-data` library for reading
- Supports batch reading for efficient processing
- Automatically handles schema inference
- Converts Vortex arrays to Python dictionaries via PyArrow
- Supports reading from files (requires file path, not streams)

### Writing

Writing support:
- Uses PyArrow Table as intermediate format
- Converts Python dictionaries to PyArrow Tables
- Writes using `vortex-data` library
- Buffers records before writing for efficiency
- Requires file path (stream mode not supported)

### Key Features

- **Columnar storage**: Efficient for analytical queries
- **Fast random access**: Better than Parquet for random row access
- **Selective reading**: Supports reading specific rows using indices
- **Compression**: Built-in compression support
- **Batch processing**: Efficient batch reading and writing
- **Totals support**: Can count total rows
- **Type preservation**: Maintains data types through PyArrow

## Dependencies

Vortex format support requires:
- `vortex-data>=0.56.0` - Core Vortex library
- `pyarrow>=10.0.0` - For data conversion (usually already installed)

**Note**: `vortex-data` requires Python ≥3.11. If you're using Python 3.10, the library will raise a clear error message when attempting to use Vortex format.

Install with:
```bash
pip install iterabledata[vortex]
```

## Usage

```python
from iterable import open_iterable

# Recommended: Using context manager (automatic cleanup)
# Basic reading
with open_iterable('data.vortex') as source:
    for row in source:
        print(row)
# File automatically closed

# Writing
with open_iterable('output.vortex', mode='w', iterableargs={
    'batch_size': 1024  # Batch size for writing
}) as dest:
    dest.write({'id': 1, 'name': 'John'})
# File automatically closed

# Bulk writing (recommended for better performance)
with open_iterable('output.vortex', mode='w', iterableargs={
    'batch_size': 1024
}) as dest:
    records = [
        {'id': 1, 'name': 'John', 'age': 30},
        {'id': 2, 'name': 'Jane', 'age': 25}
    ]
    dest.write_bulk(records)
# File automatically closed

# Alternative: Manual close (still supported)
source = open_iterable('data.vortex')
try:
    for row in source:
        print(row)
finally:
    source.close()

# Reading with totals
with open_iterable('data.vortex') as source:
    total = source.totals()
    print(f"Total rows: {total}")
    for row in source:
        print(row)

# Reset to beginning
with open_iterable('data.vortex') as source:
    row1 = source.read()
    source.reset()  # Go back to beginning
    row2 = source.read()  # Same as row1
```

## Format Detection

Vortex files are automatically detected by:
- File extension: `.vortex` or `.vtx`
- Magic number: Files starting with `VTXF` bytes

```python
# Automatic detection by extension
with open_iterable('data.vortex') as source:
    # Automatically uses VortexIterable
    pass

# Automatic detection by magic number (even without extension)
with open_iterable('data.unknown') as source:
    # If file starts with VTXF, automatically detected as Vortex
    pass
```

## Limitations

- **Stream mode not supported**: Vortex requires a file path, not a file-like stream object
- **Python version**: Requires Python ≥3.11 for `vortex-data` package
- **File path required**: Cannot use in-memory streams or file objects

## Error Handling

If `vortex-data` is not installed, you'll get a clear error message:

```python
try:
    with open_iterable('data.vortex') as source:
        pass
except ImportError as e:
    print(e)  # "Vortex support requires 'vortex-data' package. Install it with: pip install iterabledata[vortex]"
```

## Performance Considerations

- Vortex provides fast random access compared to Parquet
- Batch reading and writing improves performance
- Use `write_bulk()` instead of multiple `write()` calls
- Adjust `batch_size` based on your data characteristics

## See Also

- [Vortex Documentation](https://docs.vortex.dev/)
- [Vortex File Format Specification](https://docs.vortex.dev/specs/file-format.html)
- [PyArrow Documentation](https://arrow.apache.org/docs/python/)
