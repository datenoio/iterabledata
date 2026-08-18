# TFRecord Format (TensorFlow)

## Description

TFRecord is a binary file format used by TensorFlow for storing training data. It's designed for efficient reading of large datasets. TFRecord files contain serialized protocol buffer messages with CRC32 checksums.

## File Extensions

- `.tfrecord` - TFRecord files
- `.tfrecords` - TFRecord files (alias)

## Implementation Details

### Reading

The TFRecord implementation:
- Parses TFRecord format
- Reads length-prefixed records with CRC32 checksums
- Handles binary record data
- Converts records to dictionaries
- Supports streaming for large files

### Writing

Writing is not currently supported for TFRecord format.

### Key Features

- **TensorFlow format**: Designed for TensorFlow
- **CRC32 checksums**: Includes data integrity checks
- **Length-prefixed**: Records prefixed with length
- **Nested data**: Supports complex data structures
- **Streaming**: Processes files record by record

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('data.tfrecord', iterableargs={
    'value_key': 'value'
})
for record in source:
    print(record)  # Contains record data
source.close()
```

## Parameters

- `value_key` (str): Key name for record value (default: `value`)

## Limitations

1. **Read-only**: TFRecord format does not support writing
2. **Binary format**: Not human-readable
3. **TensorFlow-specific**: Designed for TensorFlow
4. **CRC32 validation**: Simplified CRC32 implementation
5. **Format complexity**: TFRecord format can be complex

## Compression Support

TFRecord files can be compressed with all supported codecs:
- GZip (`.tfrecord.gz`)
- BZip2 (`.tfrecord.bz2`)
- LZMA (`.tfrecord.xz`)
- LZ4 (`.tfrecord.lz4`)
- ZIP (`.tfrecord.zip`)
- Brotli (`.tfrecord.br`)
- ZStandard (`.tfrecord.zst`)

Note: TFRecord also supports internal compression.

## Use Cases

- **Machine learning**: Training data for TensorFlow
- **Data pipelines**: TensorFlow data processing
- **Model training**: Preparing training datasets
- **Data storage**: Efficient storage of training data

## Related Formats

- [Protocol Buffers](protobuf.md) - Base format used by TFRecord
- [Parquet](parquet.md) - Another ML data format
