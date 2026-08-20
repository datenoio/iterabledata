# Apache Kafka message dump

## Description

This reader/writer stores a **simplified on-disk dump** of Kafka-like messages (offset, timestamp, key, value, optional headers). It is **not** a Kafka broker client: it does not connect to a cluster and does not use `kafka-python`.

## File Extensions

- No dedicated extension. Pass `format="kafka"` (or a `.kafka` filename) to `open_iterable()`.

## Implementation Details

### Reading

- Parses a length-prefixed binary dump
- Extracts offset, timestamp, key, value, and headers
- Converts each message to a dictionary
- Optional metadata via `include_metadata`

### Writing

- Writes the same dump format
- Nested values are JSON-encoded

### Key Features

- **On-disk dump**: File-based, not a live consumer/producer
- **Key/value records**: Configurable field names
- **Metadata**: Offset, timestamp, partition when enabled

## Usage

```python
from iterable import open_iterable

with open_iterable("messages.kafka", format="kafka", iterableargs={
    "key_name": "key",
    "value_name": "value",
    "include_metadata": True,
}) as source:
    for message in source:
        print(message)

with open_iterable("output.kafka", mode="w", format="kafka") as dest:
    dest.write({
        "key": "message-key",
        "value": {"data": "message content"},
        "offset": 0,
        "timestamp": 1234567890000,
    })
```

## Parameters

- `key_name` (str): Key name for message key (default: `key`)
- `value_name` (str): Key name for message value (default: `value`)
- `include_metadata` (bool): Include offset, timestamp, partition (default: `True`)

## Limitations

1. **Not a Kafka client**: Does not speak the Kafka protocol or connect to brokers
2. **Simplified framing**: Not wire-compatible with official Kafka log segments
3. **Binary dump**: Not human-readable

## Compression Support

The dump file can be wrapped with the usual codecs (`.kafka.gz`, `.kafka.zst`, and similar).

## Related Formats

- [Pulsar](pulsar.md) - Similar on-disk message dump
- [MessagePack](msgpack.md) - Binary message format
