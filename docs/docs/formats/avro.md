# Apache Avro Format

## Description

Apache Avro is a data serialization system that provides rich data structures, compact binary format, and schema evolution. Avro files contain both the schema and data, making them self-describing. The format is widely used in big data ecosystems, particularly with Apache Hadoop and Kafka.

## File Extensions

- `.avro` - Apache Avro files

## Implementation Details

### Reading

The Avro implementation:
- Uses `avro-python3` library
- Reads Avro data files with embedded schema
- Supports schema evolution
- Converts Avro records to Python dictionaries

### Writing

Writing is not currently supported for Avro format.

### Key Features

- **Schema evolution**: Supports schema changes over time
- **Compact binary**: Efficient storage format
- **Self-describing**: Schema embedded in file
- **Type preservation**: Maintains data types
- **Flat data**: Designed for tabular/flat data structures

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.avro') as source:
    for row in source:
        print(row)
```

## Parameters

No specific parameters required for reading.

## Limitations

1. **Read-only**: Avro format does not support writing
2. **avro-python3 dependency**: Requires `avro-python3` package
3. **Flat data only**: Designed for tabular data structures
4. **Schema complexity**: Complex schemas may require manual handling
5. **Binary format**: Not human-readable

## Compression Support

Avro files can be compressed with all supported codecs:
- GZip (`.avro.gz`)
- BZip2 (`.avro.bz2`)
- LZMA (`.avro.xz`)
- LZ4 (`.avro.lz4`)
- ZIP (`.avro.zip`)
- Brotli (`.avro.br`)
- ZStandard (`.avro.zst`)

Note: Avro also has built-in compression (null, deflate, snappy), which is separate from file-level compression.

## Use Cases

- **Big data processing**: Common in Hadoop ecosystems
- **Data pipelines**: Schema evolution in streaming systems
- **Kafka**: Message serialization format
- **Data warehousing**: Efficient storage for analytics

## Related Formats

- [Parquet](parquet.md) - Another columnar format
- [ORC](orc.md) - Similar columnar format
- [Protocol Buffers](protobuf.md) - Another serialization format
