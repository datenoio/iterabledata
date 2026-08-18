# Parquet Format

## Description

Apache Parquet is a columnar storage format optimized for analytics workloads. It provides efficient compression and encoding schemes, making it ideal for large-scale data processing. Parquet files store data in a column-oriented format, which enables efficient compression and fast columnar access.

## File Extensions

- `.parquet` - Apache Parquet files

## Implementation Details

### Reading

The Parquet implementation:
- Uses PyArrow library for reading
- Supports batch reading for efficient processing
- Automatically handles schema inference
- Can read specific columns (projection pushdown)
- Supports reading from compressed files

### Writing

Writing support:
- Uses PyArrow for writing
- Supports schema adaptation (automatically infers schema from data)
- Can use pandas for schema inference
- Supports compression (default: snappy)
- Buffers records before writing for efficiency

### Key Features

- **Columnar storage**: Efficient for analytical queries
- **Compression**: Built-in compression support (snappy, gzip, brotli, lz4, zstd)
- **Schema evolution**: Can adapt schema from data
- **Batch processing**: Efficient batch reading and writing
- **Totals support**: Can count total rows efficiently
- **Type preservation**: Maintains data types

## Usage

```python
from iterable import open_iterable

# Recommended: Using context manager (automatic cleanup)
# Basic reading
with open_iterable('data.parquet') as source:
    for row in source:
        print(row)
# File automatically closed

# Writing with options
with open_iterable('output.parquet', mode='w', iterableargs={
    'compression': 'snappy',  # or 'gzip', 'brotli', 'lz4', 'zstd'
    'use_pandas': True,       # Use pandas for schema inference
    'adapt_schema': True,     # Automatically adapt schema
    'batch_size': 10000       # Batch size for writing
}) as dest:
    dest.write({'id': 1, 'name': 'John'})
# File automatically closed

# Bulk writing (recommended for better performance)
with open_iterable('output.parquet', mode='w', iterableargs={
    'compression': 'snappy',
    'adapt_schema': True,
    'batch_size': 10000
}) as dest:
    records = [
        {'id': 1, 'name': 'John', 'age': 30},
        {'id': 2, 'name': 'Jane', 'age': 25}
    ]
    dest.write_bulk(records)
# File automatically closed

# Alternative: Manual close (still supported)
source = open_iterable('data.parquet')
try:
    for row in source:
        print(row)
finally:
    source.close()
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `compression` | str | `snappy` | No | Compression codec. Options: `snappy` (fast, good balance), `gzip` (good compression), `brotli` (excellent compression), `lz4` (very fast), `zstd` (balanced), `uncompressed` |
| `use_pandas` | bool | `True` | No | Use pandas for schema inference. Set to `False` to use PyArrow directly. |
| `adapt_schema` | bool | `True` | No | Automatically adapt schema from data. If `False`, must provide `keys` or `schema` parameter. |
| `batch_size` | int | `1024` | No | Batch size for reading/writing. Larger values improve performance but use more memory. Recommended: 10,000-50,000 for writing. |
| `keys` | list | None | Yes* | Column names. Required if `adapt_schema=False`. When `adapt_schema=True`, column names are inferred from first batch of data. |
| `schema` | list | None | No | PyArrow schema definition. Advanced option for explicit schema control. |

\* Required when `adapt_schema=False`, optional when `adapt_schema=True`

## Error Handling

```python
from iterable import open_iterable

try:
    # Reading with error handling
    with open_iterable('data.parquet') as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("Parquet file not found")
except Exception as e:
    print(f"Error reading Parquet: {e}")

try:
    # Writing with error handling
    with open_iterable('output.parquet', mode='w', iterableargs={
        'adapt_schema': True,
        'compression': 'snappy'
    }) as dest:
        dest.write({'id': 1, 'name': 'John'})
except KeyError as e:
    print(f"Schema mismatch: {e}")
    # If adapt_schema=False, ensure all records have same keys
except Exception as e:
    print(f"Error writing Parquet: {e}")
```

### Common Errors

- **Schema mismatch**: When `adapt_schema=False`, all records must have the same keys. Use `adapt_schema=True` or ensure consistent structure.
- **Missing PyArrow**: Install `pyarrow` package: `pip install pyarrow`
- **Write buffering**: Records are buffered - call `close()` or use context manager to ensure data is written

## Limitations

1. **Flat data only**: Parquet is designed for tabular/flat data structures
2. **PyArrow dependency**: Requires `pyarrow` package
3. **Schema complexity**: Complex nested schemas may require manual definition
4. **Write buffering**: Records are buffered before writing (call `close()` to flush)
5. **No streaming writes**: Schema must be known before writing (unless using adapt_schema)

## Compression Support

Parquet has built-in compression support:
- Snappy (default, fast compression)
- GZip (good compression ratio)
- Brotli (excellent compression ratio)
- LZ4 (very fast compression)
- ZStandard (balanced compression)

Note: Parquet compression is different from file-level compression codecs. You can use both together (e.g., `data.parquet.gz`).

## Performance Considerations

### Performance Tips

- **Use bulk operations**: Use `write_bulk()` instead of individual `write()` calls for significantly better performance
  ```python
  # Recommended: Bulk write
  with open_iterable('output.parquet', mode='w', iterableargs={
      'batch_size': 10000
  }) as dest:
      dest.write_bulk(records)  # Much faster than individual writes
  ```

- **Batch size**: Larger batch sizes improve performance but use more memory
  - Reading: Default 1024 is usually sufficient
  - Writing: Recommended 10,000-50,000 for best performance
  - Very large batches (100,000+) may cause memory issues

- **Compression**: Choose compression based on your needs
  - `snappy`: Fast compression, good balance (recommended default)
  - `gzip`: Good compression ratio, slower than snappy
  - `brotli`: Excellent compression, slower
  - `lz4`: Very fast, lower compression
  - `zstd`: Balanced compression and speed

- **Schema adaptation**: Automatic schema adaptation has overhead on first write
  - For consistent data, set `adapt_schema=False` and provide `keys` for better performance
  - For variable schemas, `adapt_schema=True` is more flexible but slower

- **Column projection**: Reading only needed columns improves performance (future enhancement)

- **Memory usage**: Parquet files are processed in batches, making them memory-efficient for large files

## Use Cases

- **Data warehousing**: Storing large analytical datasets
- **ETL pipelines**: Intermediate format for data transformation
- **Data lake storage**: Efficient storage for data lakes
- **Analytics**: Fast columnar queries

## Related Formats

- [Arrow](arrow.md) - Similar columnar format (Feather)
- [ORC](orc.md) - Another columnar format
- [Delta Lake](delta.md) - Transactional layer over Parquet
