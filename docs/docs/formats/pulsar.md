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
- UTF-8 text is JSON-decoded when possible; otherwise kept as a string (binary payloads become base64)
- Optional metadata via `include_metadata`

### Writing

- Writes the same dump format
- Nested values (dict/list) are JSON-encoded
- `message_id` defaults to `msg_{pos}` when omitted; `publish_time` defaults to `0`

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

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `key_name` | str | `"key"` | No | Dict key for the message key |
| `value_name` | str | `"value"` | No | Dict key for the message payload |
| `include_metadata` | bool | `True` | No | Include `message_id`, `publish_time`, and `properties` when present |

## Error Handling

- **FormatParseError**: Truncated or corrupt dump framing while reading
- **FileNotFoundError**: Path is wrong or the file is missing
- No optional dependency — missing Pulsar client libraries are expected (this is not a broker client)

See [Troubleshooting](/getting-started/troubleshooting) for more help.

## Limitations

1. **Not a Pulsar client**: Does not speak the Pulsar protocol or connect to brokers
2. **Simplified framing**: Not wire-compatible with official Pulsar ledgers
3. **Binary dump**: Not human-readable

## Compression Support

The dump file can be wrapped with the usual codecs (`.pulsar.gz`, `.pulsar.zst`, and similar).

## Related Formats

- [Kafka](kafka.md) - Similar on-disk message dump
- [MessagePack](msgpack.md) - Binary message format
