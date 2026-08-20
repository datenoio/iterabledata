# Apache Pulsar Format

## Description

Apache Pulsar is a distributed messaging and streaming platform. This implementation handles Pulsar message format for reading/writing Pulsar messages. Pulsar messages contain message ID, publish time, key, properties, and payload.

## File Extensions

- No specific extension (Pulsar data files)

## Implementation Details

### Reading

The Pulsar implementation:
- Parses Pulsar message format
- Extracts message ID, publish time, key, properties, and payload
- Handles binary message data
- Converts messages to dictionaries
- Supports metadata inclusion/exclusion

### Writing

Writing support:
- Writes Pulsar message format
- Includes message ID, publish time, key, properties, and payload
- Writes binary message data

### Key Features

- **Message format**: Handles Pulsar message structure
- **Metadata support**: Includes message ID, publish time, properties
- **Key-value**: Supports message keys and values
- **Properties**: Handles message properties
- **Nested data**: Supports complex message structures

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('pulsar.data', iterableargs={
    'key_name': 'key',
    'value_name': 'value',
    'include_metadata': True
}) as source:
    for message in source:
        print(message)  # Contains key, value, message_id, publish_time, etc.

# Writing
with open_iterable('output.pulsar', mode='w') as dest:
    dest.write({
        'key': 'message-key',
        'value': {'data': 'message content'},
        'message_id': 'msg-123',
        'publish_time': 1234567890000
    })
```

## Parameters

- `key_name` (str): Key name for message key (default: `key`)
- `value_name` (str): Key name for message value (default: `value`)
- `include_metadata` (bool): Include message_id, publish_time, properties (default: `True`)

## Limitations

1. **Binary format**: Not human-readable
2. **Pulsar-specific**: Designed for Pulsar message format
3. **Format complexity**: Pulsar message format can be complex
4. **Simplified implementation**: May not support all Pulsar features

## Compression Support

Pulsar files can be compressed with all supported codecs:
- GZip (`.pulsar.gz`)
- BZip2 (`.pulsar.bz2`)
- LZMA (`.pulsar.xz`)
- LZ4 (`.pulsar.lz4`)
- ZIP (`.pulsar.zip`)
- Brotli (`.pulsar.br`)
- ZStandard (`.pulsar.zst`)

Note: Pulsar also has built-in compression.

## Use Cases

- **Streaming data**: Processing Pulsar message streams
- **Event sourcing**: Event sourcing systems
- **Real-time processing**: Real-time data processing
- **Message queues**: Working with message queue data

## Related Formats

- [Kafka](kafka.md) - Apache Kafka format
- [MessagePack](msgpack.md) - Binary message format
