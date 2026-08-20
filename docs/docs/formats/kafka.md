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
- UTF-8 text is JSON-decoded when possible; otherwise kept as a string (binary payloads become base64)
- Optional metadata via `include_metadata`

### Writing

- Writes the same dump format
- Nested values (dict/list) are JSON-encoded
- Offset defaults to previous + 1 when omitted; timestamp defaults to `0`

### Key Features

- **On-disk dump**: File-based, not a live consumer/producer
- **Key/value records**: Configurable field names
- **Metadata**: Offset, timestamp, headers when enabled

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

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `key_name` | str | `"key"` | No | Dict key for the message key |
| `value_name` | str | `"value"` | No | Dict key for the message value |
| `include_metadata` | bool | `True` | No | Include `offset`, `timestamp`, and `headers` when present |

## Error Handling

- **FormatParseError**: Truncated or corrupt dump framing while reading
- **FileNotFoundError**: Path is wrong or the file is missing
- No optional dependency — missing Kafka client libraries are expected (this is not a broker client)

See [Troubleshooting](/getting-started/troubleshooting) for more help.

## Limitations

1. **Not a Kafka client**: Does not speak the Kafka protocol or connect to brokers
2. **Simplified framing**: Not wire-compatible with official Kafka log segments
3. **Binary dump**: Not human-readable

## Compression Support

The dump file can be wrapped with the usual codecs (`.kafka.gz`, `.kafka.zst`, and similar).

## Related Formats

- [Pulsar](pulsar.md) - Similar on-disk message dump
- [MessagePack](msgpack.md) - Binary message format
