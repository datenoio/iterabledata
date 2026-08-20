# Lance Format

## Description

Lance is a modern columnar data format designed to optimize machine learning (ML) and data science workflows. It offers high-performance random access, efficient vector search capabilities, automatic versioning, and seamless integration with tools like Pandas, DuckDB, and Polars. Lance is built on Apache Arrow and provides faster point queries compared to traditional formats like Parquet.

## File Extensions

- `.lance` - Lance dataset (directory-based format)

**Note**: Lance datasets are stored as directories, not single files. When you specify a filename ending with `.lance`, the extension is removed to get the directory path.

## Implementation Details

### Reading

The Lance implementation:
- Uses the `lance` Python library for reading
- Opens Lance datasets as directories
- Supports batch reading for efficient iteration
- Preserves data types and schema
- Provides fast random access to data

### Writing

Writing support:
- Buffers records before writing
- Uses `lance.write_dataset()` for creating datasets
- Supports multiple write modes: 'create', 'overwrite', 'append'
- Flushes data on close
- Maintains schema from data

### Key Features

- **Columnar format**: Efficient for analytical and ML workloads
- **Vector search**: Built-in support for similarity search over embedding spaces
- **Fast random access**: Significantly faster point queries than Parquet
- **Automatic versioning**: Supports dataset versioning and time-travel capabilities
- **High performance**: Optimized for ML and data science workflows
- **Totals support**: Can count total rows efficiently
- **Batch processing**: Efficient batch reading and writing
- **Type preservation**: Maintains data types

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.lance') as source:
    for row in source:
        print(row)

# Writing with options
dest = open_iterable('output.lance', mode='w', iterableargs={
    'batch_size': 10000,
    'write_mode': 'create'  # or 'overwrite', 'append'
})
dest.write({'id': 1, 'name': 'John', 'age': 30})
dest.close()  # Important: closes and flushes data

# Bulk writing
with open_iterable('output.lance', mode='w') as dest:
    records = [
        {'id': 1, 'name': 'Alice', 'age': 25},
        {'id': 2, 'name': 'Bob', 'age': 30},
        {'id': 3, 'name': 'Charlie', 'age': 35}
    ]
    dest.write_bulk(records)
```

## Parameters

- `batch_size` (int): Batch size for reading (default: `1024`)
- `write_mode` (str): Write mode for creating datasets (default: `'create'`)
  - `'create'`: Creates a new dataset (raises error if exists)
  - `'overwrite'`: Creates a new snapshot version, replacing existing dataset
  - `'append'`: Appends new data to the latest version

## Limitations

1. **Lance dependency**: Requires `lance` package (`pip install lance`)
2. **Directory-based**: Lance datasets are directories, not single files
3. **Flat data only**: Designed for tabular/flat data structures
4. **Write buffering**: Must call `close()` to flush buffered data
5. **PyArrow dependency**: Requires `pyarrow` (installed with lance)

## Compression Support

Lance format has built-in compression and optimization. Note that Lance datasets are directories, so file-level compression codecs (like `.gz`) are not applicable in the same way as single-file formats.

## Performance Considerations

- **Fast random access**: Lance provides significantly faster point queries than Parquet
- **Vector search**: Built-in support for efficient similarity search
- **Batch size**: Larger batch sizes improve iteration performance
- **Memory efficiency**: Optimized for large-scale ML workflows
- **Versioning**: Automatic versioning enables time-travel queries

## Use Cases

- **Machine learning**: Optimized format for ML data pipelines
- **Vector search**: Similarity search over embedding spaces
- **Data science**: High-performance data processing workflows
- **Analytics**: Fast columnar data access with random access capabilities
- **Data versioning**: Automatic versioning for reproducible ML experiments


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [Parquet](parquet.md) - Similar columnar format (Lance is faster for random access)
- [Arrow](arrow.md) - In-memory columnar format (Lance is built on Arrow)
- [ORC](orc.md) - Another columnar format

## Installation

To use Lance format, install the required package:

```bash
pip install lance
```

The `lance` package includes `pyarrow` as a dependency, so you don't need to install it separately.
