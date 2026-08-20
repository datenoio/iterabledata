# Apache Avro Format

## Description

Apache Avro is a data serialization system that provides rich data structures, compact binary format, and schema evolution. Avro files contain both the schema and data, making them self-describing. The format is widely used in big data ecosystems, particularly with Apache Hadoop and Kafka.

## File Extensions

- `.avro` - Apache Avro files

## Implementation Details

### Reading

The Avro implementation:
- Uses the `avro` package
- Reads Avro data files with embedded schema
- Supports schema evolution
- Converts Avro records to Python dictionaries

### Writing

Writing support:
- Infers an Avro schema from the first record
- Appends records with the `avro` package (`pip install iterabledata[avro]`)
- Coerces values to match the schema

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

# Writing
with open_iterable('output.avro', mode='w') as dest:
    dest.write({'name': 'John', 'age': 30})
```

## Parameters

No specific parameters required for reading.

## Limitations

1. **Avro extra**: Requires `pip install iterabledata[avro]` (`avro`)
2. **Flat data only**: Designed for tabular data structures
3. **Schema complexity**: Complex schemas may require manual handling
4. **Binary format**: Not human-readable

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
