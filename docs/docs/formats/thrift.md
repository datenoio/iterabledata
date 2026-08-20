# Apache Thrift Format

## Description

Apache Thrift is a cross-language serialization framework. It allows you to define data types and service interfaces in a definition file, then generate code for various languages. Thrift provides efficient binary serialization.

## File Extensions

- `.thrift` - Thrift files (schema definition files)
- Binary Thrift data files (no standard extension)

## Implementation Details

### Reading

The Thrift implementation:
- Uses `thrift` library for reading
- Requires `struct_class` parameter (the generated Thrift struct class)
- Reads binary Thrift data
- Converts Thrift structs to Python dictionaries
- Supports multiple serialized structs in one file

### Writing

Writing support:
- Serializes Python dictionaries to Thrift format
- Requires `struct_class` parameter
- Writes binary Thrift data

### Key Features

- **Schema-based**: Requires generated struct classes from .thrift files
- **Binary format**: Efficient binary serialization
- **Cross-language**: Compatible with many programming languages
- **Nested data**: Supports complex nested structures
- **Type preservation**: Maintains data types

## Usage

```python
from iterable import open_iterable
from my_thrift_module import MyStruct  # Generated from .thrift file

# Reading
with open_iterable('data.thrift', iterableargs={
    'struct_class': MyStruct
}) as source:
    for row in source:
        print(row)  # row is a dict

# Writing
with open_iterable('output.thrift', mode='w', iterableargs={
    'struct_class': MyStruct
}) as dest:
    dest.write({'field1': 'value1', 'field2': 123})
```

## Parameters

- `struct_class`: **Required** - The generated Thrift struct class from .thrift file

## Limitations

1. **thrift dependency**: Requires `thrift` package
2. **Schema required**: Must have generated struct classes from .thrift files
3. **Binary format**: Not human-readable
4. **Struct class required**: Cannot work without the struct class
5. **File structure**: Expects sequential Thrift structs

## Compression Support

Thrift files can be compressed with all supported codecs:
- GZip (`.thrift.gz`)
- BZip2 (`.thrift.bz2`)
- LZMA (`.thrift.xz`)
- LZ4 (`.thrift.lz4`)
- ZIP (`.thrift.zip`)
- Brotli (`.thrift.br`)
- ZStandard (`.thrift.zst`)

## Use Cases

- **Cross-language services**: Inter-service communication
- **RPC frameworks**: Remote procedure calls
- **Data serialization**: Efficient data exchange
- **Microservices**: Service-to-service data exchange

## Related Formats

- [Protocol Buffers](protobuf.md) - Similar schema-based format
- [Cap'n Proto](capnp.md) - Another schema-based format
- [Avro](avro.md) - Another serialization format
