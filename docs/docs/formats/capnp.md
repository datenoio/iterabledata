# Cap'n Proto Format

## Description

Cap'n Proto is a fast data interchange format and capability-based RPC system. It's designed to be faster than Protocol Buffers and supports zero-copy reads. Cap'n Proto uses schema files to define data structures.

## File Extensions

- `.capnp` - Cap'n Proto schema files
- Binary Cap'n Proto data files (no standard extension)

## Implementation Details

### Reading

The Cap'n Proto implementation:
- Uses `pycapnp` library for reading
- Requires `schema_file` and `schema_name` parameters
- Loads schema from .capnp file
- Reads binary Cap'n Proto data
- Converts messages to Python dictionaries

### Writing

Writing support:
- Serializes Python dictionaries to Cap'n Proto format
- Requires `schema_file` and `schema_name` parameters
- Writes binary Cap'n Proto data

### Key Features

- **Schema-based**: Requires schema file and message type name
- **Fast serialization**: Zero-copy reads possible
- **Binary format**: Efficient binary serialization
- **Nested data**: Supports complex nested structures
- **Type preservation**: Maintains data types

## Usage

```python
from iterable import open_iterable

# Reading
with open_iterable('data.capnp', iterableargs={
    'schema_file': 'schema.capnp',
    'schema_name': 'MyMessage'
}) as source:
    for row in source:
        print(row)

# Writing
with open_iterable('output.capnp', mode='w', iterableargs={
    'schema_file': 'schema.capnp',
    'schema_name': 'MyMessage'
}) as dest:
    dest.write({'field1': 'value1', 'field2': 123})
```

## Parameters

- `schema_file` (str): **Required** - Path to .capnp schema file
- `schema_name` (str): **Required** - Name of the message type in the schema

## Limitations

1. **pycapnp dependency**: Requires `pycapnp` package
2. **Schema required**: Must have schema file and message type name
3. **Binary format**: Not human-readable
4. **Schema complexity**: Complex schemas may require manual handling
5. **File structure**: Expects sequential Cap'n Proto messages

## Compression Support

Cap'n Proto files can be compressed with all supported codecs:
- GZip (`.capnp.gz`)
- BZip2 (`.capnp.bz2`)
- LZMA (`.capnp.xz`)
- LZ4 (`.capnp.lz4`)
- ZIP (`.capnp.zip`)
- Brotli (`.capnp.br`)
- ZStandard (`.capnp.zst`)

## Use Cases

- **High-performance RPC**: Fast inter-service communication
- **Data serialization**: Efficient data exchange
- **Real-time systems**: Low-latency data processing
- **Gaming**: Fast data serialization

## Related Formats

- [Protocol Buffers](protobuf.md) - Similar schema-based format
- [Thrift](thrift.md) - Apache Thrift format
- [FlatBuffers](flatbuffers.md) - Another fast serialization format
