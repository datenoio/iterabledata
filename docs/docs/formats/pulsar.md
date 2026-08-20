# Apache Pulsar message dump

## Description

This reader/writer stores a **simplified on-disk dump** of Pulsar-like messages (message id, publish time, key, properties, payload). It is **not** a Pulsar client: it does not connect to a cluster and does not use `pulsar-client`.

## File Extensions

- No dedicated extension. Pass `format="pulsar"` (or a `.pulsar` filename) to `open_iterable()`.

## Implementation Details

### Reading

- Parses a length-prefixed binary dump
- Extracts message id, publish time, key, properties, and payload
- Converts each message to a dictionary

### Writing

- Writes the same dump format
- Nested values are JSON-encoded

### Key Features

- **On-disk dump**: File-based, not a live consumer/producer
- **Key/value records**: Configurable field names
- **Metadata**: Message id, publish time, properties when enabled

## Usage

```python
from iterable import open_iterable

with open_iterable("messages.pulsar", format="pulsar", iterableargs={
    "key_name": "key",
    "value_name": "value",
    "include_metadata": True,
}) as source:
    for message in source:
        print(message)

with open_iterable("output.pulsar", mode="w", format="pulsar") as dest:
    dest.write({
        "key": "message-key",
        "value": {"data": "message content"},
        "message_id": "msg-123",
        "publish_time": 1234567890000,
    })
```

## Parameters

- `key_name` (str): Key name for message key (default: `key`)
- `value_name` (str): Key name for message value (default: `value`)
- `include_metadata` (bool): Include message_id, publish time, properties (default: `True`)

## Limitations

1. **Not a Pulsar client**: Does not speak the Pulsar protocol or connect to brokers
2. **Simplified framing**: Not wire-compatible with official Pulsar ledgers
3. **Binary dump**: Not human-readable

## Compression Support

The dump file can be wrapped with the usual codecs (`.pulsar.gz`, `.pulsar.zst`, and similar).

## Related Formats

- [Kafka](kafka.md) - Similar on-disk message dump
- [MessagePack](msgpack.md) - Binary message format
