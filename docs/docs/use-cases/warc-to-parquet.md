---
sidebar_position: 5
title: WARC to Parquet Conversion
description: Convert compressed WARC archives to Parquet format for efficient analytics
---

# WARC to Parquet Conversion

This guide demonstrates how to convert compressed WARC (Web ARChive) files to Parquet format for efficient storage and analytics. WARC files are commonly used for web archiving and can be very large, making Parquet an ideal format for analytical queries and data processing.

## Overview

WARC files contain web archive data including HTTP requests, responses, and metadata. Converting them to Parquet format provides:

1. **Efficient storage**: Columnar format with built-in compression
2. **Fast queries**: Optimized for analytical workloads
3. **Schema preservation**: Maintains data structure for analysis
4. **Compression**: Multiple compression options (snappy, gzip, zstd, etc.)

## Simple Conversion

The simplest way to convert a WARC.gz file to compressed Parquet:

```python
from iterable.convert import convert

# Convert WARC.gz to Parquet with compression
convert(
    'archive.warc.gz',
    'archive.parquet',
    iterableargs={'compression': 'snappy'}  # Parquet compression
)
```

The `convert()` function automatically:
- Detects WARC format from `.warc` extension
- Handles GZip compression from `.gz` extension
- Detects Parquet format from `.parquet` extension
- Applies Parquet compression

## Conversion with Compression Options

You can specify different compression codecs for Parquet:

```python
from iterable.convert import convert

# Convert with ZStandard compression (better compression ratio)
convert(
    'archive.warc.gz',
    'archive.parquet',
    iterableargs={'compression': 'zstd'},
    batch_size=50000
)

# Convert with GZip compression (balanced)
convert(
    'archive.warc.gz',
    'archive.parquet',
    iterableargs={'compression': 'gzip'},
    batch_size=50000
)

# Convert with Brotli compression (best compression)
convert(
    'archive.warc.gz',
    'archive.parquet',
    iterableargs={'compression': 'brotli'},
    batch_size=50000
)
```

## Manual Conversion

For more control over the conversion process:

```python
from iterable import open_iterable

# Open compressed WARC file
source = open_iterable('archive.warc.gz')

# Open Parquet file with compression
destination = open_iterable(
    'archive.parquet',
    mode='w',
    iterableargs={
        'compression': 'snappy',  # or 'gzip', 'zstd', 'brotli', 'lz4'
        'adapt_schema': True,     # Automatically adapt schema from data
        'batch_size': 10000       # Batch size for writing
    }
)

# Convert records
for record in source:
    destination.write(record)

source.close()
destination.close()
```

## Batch Processing

For large WARC files, use batch processing for better memory efficiency:

```python
from iterable import open_iterable

source = open_iterable('archive.warc.gz')
destination = open_iterable(
    'archive.parquet',
    mode='w',
    iterableargs={
        'compression': 'zstd',
        'adapt_schema': True,
        'batch_size': 50000
    }
)

batch = []
for record in source:
    batch.append(record)
    if len(batch) >= 50000:
        destination.write_bulk(batch)
        batch = []

if batch:
    destination.write_bulk(batch)

source.close()
destination.close()
```

## Using Different Compression Formats

WARC files can be compressed with various codecs. Iterable Data handles them automatically:

```python
from iterable.convert import convert

# GZip compressed WARC
convert('archive.warc.gz', 'output.parquet', 
        iterableargs={'compression': 'snappy'})

# BZip2 compressed WARC
convert('archive.warc.bz2', 'output.parquet',
        iterableargs={'compression': 'snappy'})

# ZStandard compressed WARC
convert('archive.warc.zst', 'output.parquet',
        iterableargs={'compression': 'snappy'})

# Uncompressed WARC
convert('archive.warc', 'output.parquet',
        iterableargs={'compression': 'snappy'})
```

## Processing WARC Records

WARC records contain various fields. You can process and filter them during conversion:

```python
from iterable import open_iterable

source = open_iterable('archive.warc.gz')
destination = open_iterable(
    'archive.parquet',
    mode='w',
    iterableargs={
        'compression': 'snappy',
        'adapt_schema': True
    }
)

for record in source:
    # Filter or transform records
    if record.get('record_type') == 'response':
        # Only convert response records
        destination.write(record)

source.close()
destination.close()
```

## Querying Converted Parquet Files

Once converted to Parquet, you can query the data efficiently:

```python
from iterable import open_iterable

# Open Parquet file
source = open_iterable('archive.parquet')

# Query specific records
for record in source:
    if 'example.com' in record.get('target_uri', ''):
        print(record)

source.close()
```

Or use DuckDB for SQL queries:

```python
import duckdb

conn = duckdb.connect()

# Query Parquet file directly
result = conn.execute("""
    SELECT target_uri, record_type, content_length
    FROM 'archive.parquet'
    WHERE record_type = 'response'
    LIMIT 100
""").fetchall()

for row in result:
    print(row)
```

## Compression Comparison

Parquet supports multiple compression codecs with different trade-offs:

| Codec    | Speed      | Compression Ratio | Use Case                    |
|----------|------------|-------------------|----------------------------|
| snappy   | Very Fast  | Good              | Default, balanced          |
| gzip     | Fast       | Better            | Good compression needed    |
| zstd     | Fast       | Excellent         | Best balance (recommended) |
| brotli   | Slower     | Best              | Maximum compression        |
| lz4      | Fastest    | Fair              | Speed priority             |

For WARC archives, `zstd` or `snappy` are recommended for a good balance of speed and compression.

## Performance Tips

1. **Batch size**: Use larger batch sizes (10,000-50,000) for better performance
2. **Compression**: ZStandard (`zstd`) provides excellent compression with good speed
3. **Schema adaptation**: Enable `adapt_schema` for automatic schema detection
4. **Progress tracking**: Use `silent=False` in `convert()` to monitor progress

```python
from iterable.convert import convert

# Convert with progress tracking
convert(
    'archive.warc.gz',
    'archive.parquet',
    iterableargs={'compression': 'zstd'},
    batch_size=50000,
    silent=False  # Show progress bar
)
```

## Complete Example

Here's a complete example that converts a WARC.gz file to compressed Parquet:

```python
from iterable.convert import convert

def convert_warc_to_parquet(input_file, output_file, compression='zstd'):
    """
    Convert WARC.gz file to compressed Parquet format.
    
    Args:
        input_file: Path to input WARC.gz file
        output_file: Path to output Parquet file
        compression: Parquet compression codec (snappy, gzip, zstd, brotli, lz4)
    """
    convert(
        input_file,
        output_file,
        iterableargs={'compression': compression},
        batch_size=50000,
        silent=False
    )
    print(f"Conversion complete: {input_file} -> {output_file}")

if __name__ == "__main__":
    convert_warc_to_parquet(
        'web-archive.warc.gz',
        'web-archive.parquet',
        compression='zstd'
    )
```

## Use Cases

- **Web archive analysis**: Convert WARC archives for analytical queries
- **Data warehousing**: Store web archive data in efficient columnar format
- **ETL pipelines**: Transform WARC data for downstream processing
- **Research**: Analyze web archive data with SQL tools
- **Compliance**: Archive web data in queryable format

## Related Topics

- [WARC Format](/formats/warc) - Learn about WARC format details
- [Parquet Format](/formats/parquet) - Learn about Parquet format
- [Format Conversion](/use-cases/format-conversion) - General format conversion guide
- [DuckDB Integration](/use-cases/duckdb-integration) - Query Parquet files with DuckDB

