# Apache Kafka Format

## Description

Apache Kafka is a distributed streaming platform. This implementation handles Kafka message format for reading/writing Kafka messages. Kafka messages contain offset, timestamp, key, value, and optional headers.

## File Extensions

- No specific extension (Kafka data files)

## Implementation Details

### Reading

The Kafka implementation:
- Parses Kafka message format
- Extracts offset, timestamp, key, value, and headers
- Handles binary message data
- Converts messages to dictionaries
- Supports metadata inclusion/exclusion

### Writing

Writing support:
- Writes Kafka message format
- Includes offset, timestamp, key, value, and headers
- Writes binary message data

### Key Features

- **Message format**: Handles Kafka message structure
- **Metadata support**: Includes offset, timestamp, partition
- **Key-value**: Supports message keys and values
- **Headers**: Handles message headers
- **Nested data**: Supports complex message structures

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('kafka.data', iterableargs={
    'key_name': 'key',
    'value_name': 'value',
    'include_metadata': True
}) as source:
    for message in source:
        print(message)  # Contains key, value, offset, timestamp, etc.

# Writing
with open_iterable('output.kafka', mode='w') as dest:
    dest.write({
        'key': 'message-key',
        'value': {'data': 'message content'},
        'offset': 0,
        'timestamp': 1234567890000
    })
```

## Parameters

- `key_name` (str): Key name for message key (default: `key`)
- `value_name` (str): Key name for message value (default: `value`)
- `include_metadata` (bool): Include offset, timestamp, partition (default: `True`)

## Limitations

1. **Binary format**: Not human-readable
2. **Kafka-specific**: Designed for Kafka message format
3. **Format complexity**: Kafka message format can be complex
4. **Simplified implementation**: May not support all Kafka features

## Compression Support

Kafka files can be compressed with all supported codecs:
- GZip (`.kafka.gz`)
- BZip2 (`.kafka.bz2`)
- LZMA (`.kafka.xz`)
- LZ4 (`.kafka.lz4`)
- ZIP (`.kafka.zip`)
- Brotli (`.kafka.br`)
- ZStandard (`.kafka.zst`)

Note: Kafka also has built-in compression (gzip, snappy, lz4, zstd).

## Use Cases

- **Streaming data**: Processing Kafka message streams
- **Event sourcing**: Event sourcing systems
- **Real-time processing**: Real-time data processing
- **Message queues**: Working with message queue data

## Related Formats

- [Pulsar](pulsar.md) - Apache Pulsar format
- [MessagePack](msgpack.md) - Binary message format
