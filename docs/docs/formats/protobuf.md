# Protocol Buffers Format

## Description

Protocol Buffers (protobuf) is a language-neutral, platform-neutral extensible mechanism for serializing structured data. It's developed by Google and is widely used for data serialization in distributed systems, APIs, and data storage.

## File Extensions

- `.pb` - Protocol Buffers files
- `.protobuf` - Protocol Buffers files (alias)

## Implementation Details

### Reading

The Protobuf implementation:
- Uses `protobuf` library for reading
- Requires `message_class` parameter (the generated message class)
- Reads messages sequentially from binary stream
- Converts protobuf messages to Python dictionaries
- Handles varint-encoded message sizes

### Writing

Writing support:
- Serializes dictionaries to protobuf messages
- Requires `message_class` parameter
- Writes varint-encoded message sizes
- Writes serialized message data

### Key Features

- **Schema-based**: Requires generated message classes from .proto files
- **Binary format**: Efficient binary serialization
- **Type preservation**: Maintains data types
- **Nested data**: Supports complex nested structures
- **Cross-language**: Compatible with many programming languages

## Usage

```python
from iterable import open_iterable
from my_proto_pb2 import MyMessage  # Generated from .proto file

# Reading
with open_iterable('data.pb', iterableargs={
    'message_class': MyMessage
}) as source:
    for row in source:
        print(row)  # row is a dict

# Writing
with open_iterable('output.pb', mode='w', iterableargs={
    'message_class': MyMessage
}) as dest:
    dest.write({'field1': 'value1', 'field2': 123})
```

## Parameters

- `message_class`: **Required** - The generated protobuf message class from .proto file

## Limitations

1. **protobuf dependency**: Requires `protobuf` package
2. **Schema required**: Must have generated message classes from .proto files
3. **Binary format**: Not human-readable
4. **Message class required**: Cannot work without the message class
5. **Varint encoding**: Simplified varint encoding implementation

## Compression Support

Protobuf files can be compressed with all supported codecs:
- GZip (`.pb.gz`)
- BZip2 (`.pb.bz2`)
- LZMA (`.pb.xz`)
- LZ4 (`.pb.lz4`)
- ZIP (`.pb.zip`)
- Brotli (`.pb.br`)
- ZStandard (`.pb.zst`)

## Use Cases

- **APIs**: Data serialization in APIs
- **Distributed systems**: Inter-service communication
- **Data storage**: Efficient binary storage
- **Microservices**: Service-to-service data exchange

## Related Formats

- [Cap'n Proto](capnp.md) - Similar schema-based format
- [Thrift](thrift.md) - Apache Thrift serialization
- [Avro](avro.md) - Another schema-based format
