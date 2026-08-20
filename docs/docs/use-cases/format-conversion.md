---
sidebar_position: 1
title: Format Conversion
description: Convert data between different file formats
---

# Format Conversion

Iterable Data makes it easy to convert data between different formats. The `convert()` function handles format detection, compression, and efficient batch processing automatically.

## Simple Conversion

The simplest way to convert between formats:

```python
from iterable.convert import convert

# Convert JSONL to Parquet
convert('input.jsonl.gz', 'output.parquet')
```

The function automatically:
- Detects input and output formats from file extensions
- Handles compression (both input and output)
- Uses efficient batch processing

## Conversion with Options

You can specify options for the conversion:

```python
from iterable.convert import convert

# Convert CSV with custom delimiter and encoding
convert(
    'input.csv.xz',
    'output.jsonl.zst',
    iterableargs={'delimiter': ';', 'encoding': 'utf-8'},
    batch_size=10000
)
```

## Flattening Nested Structures

When converting from nested formats (JSON, XML) to flat formats (CSV, Parquet), you can flatten the structure:

```python
from iterable.convert import convert

# Convert JSONL to CSV with flattening
convert(
    'input.jsonl',
    'output.csv',
    is_flatten=True,
    batch_size=50000
)
```

This will flatten nested dictionaries and arrays into dot-notation keys (e.g., `user.name`, `items.0.price`).

## Manual Conversion

For more control, you can manually read and write:

```python
from iterable import open_iterable

# Recommended: Using context managers
with open_iterable('input.jsonl.gz') as source:
    with open_iterable('output.parquet', mode='w') as destination:
        for row in source:
            destination.write(row)
# Files automatically closed
```

## Batch Processing

For large files, use bulk operations:

```python
from iterable import open_iterable

# Recommended: Using context managers
with open_iterable('input.csv') as source:
    with open_iterable('output.jsonl.zst', mode='w') as destination:
        batch = []
        for row in source:
            batch.append(row)
            if len(batch) >= 10000:
                destination.write_bulk(batch)
                batch = []
        
        if batch:
            destination.write_bulk(batch)
# Files automatically closed
```

## Compression Handling

Compression is handled automatically based on file extensions:

```python
# Input compressed, output uncompressed
convert('input.csv.gz', 'output.csv')

# Input uncompressed, output compressed
convert('input.jsonl', 'output.jsonl.zst')

# Both compressed
convert('input.csv.xz', 'output.jsonl.bz2')
```

## Supported Conversions

You can convert between any supported formats:
- **Tabular formats**: CSV, TSV, PSV, Excel (XLS/XLSX), Parquet, ORC
- **JSON formats**: JSON, JSONL, GeoJSON
- **Binary formats**: BSON, MessagePack, Avro, Arrow
- **Other formats**: XML, YAML, and 100+ more

See the [Supported Formats](/formats/) page for a complete list.

## Best Practices

1. **Use appropriate batch sizes**: Larger batch sizes (10,000-50,000) improve performance for large files
2. **Choose the right format**: Use Parquet for analytics, JSONL for streaming, CSV for compatibility
3. **Consider compression**: Compressed formats save space and often process faster
4. **Handle errors**: Always wrap conversions in try/except blocks

## Related Topics

- [Data Pipelines](/use-cases/data-pipelines) - Build data processing pipelines
- [API Reference: convert()](/api/convert) - Full API documentation
