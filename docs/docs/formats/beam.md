# Apache Beam Format

## Description

Apache Beam is a unified programming model for batch and streaming data processing. This implementation handles Beam format for reading/writing Beam data records. Beam records contain window, timestamp, key, and value.

## File Extensions

- No specific extension (Beam data files)

## Implementation Details

### Reading

The Beam implementation:
- Parses Beam record format
- Extracts window, timestamp, key, and value
- Handles binary record data
- Converts records to dictionaries
- Supports metadata inclusion/exclusion

### Writing

Writing is not currently supported for Beam format.

### Key Features

- **Record format**: Handles Beam record structure
- **Metadata support**: Includes window and timestamp
- **Key-value**: Supports record keys and values
- **Nested data**: Supports complex record structures

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('beam.data', iterableargs={
    'key_name': 'key',
    'value_name': 'value',
    'include_metadata': True
})
for record in source:
    print(record)  # Contains key, value, window, timestamp
source.close()
```

## Parameters

- `key_name` (str): Key name for record key (default: `key`)
- `value_name` (str): Key name for record value (default: `value`)
- `include_metadata` (bool): Include window, timestamp (default: `True`)

## Limitations

1. **Read-only**: Beam format does not support writing
2. **Binary format**: Not human-readable
3. **Beam-specific**: Designed for Beam record format
4. **Format complexity**: Beam format can be complex
5. **Simplified implementation**: May not support all Beam features

## Compression Support

Beam files can be compressed with all supported codecs:
- GZip (`.beam.gz`)
- BZip2 (`.beam.bz2`)
- LZMA (`.beam.xz`)
- LZ4 (`.beam.lz4`)
- ZIP (`.beam.zip`)
- Brotli (`.beam.br`)
- ZStandard (`.beam.zst`)

## Use Cases

- **Stream processing**: Processing Beam data streams
- **Batch processing**: Processing Beam batch data
- **Data pipelines**: Beam data processing pipelines
- **ETL operations**: ETL with Beam

## Related Formats

- [Kafka](kafka.md) - Apache Kafka format
- [Flink](flink.md) - Apache Flink format
