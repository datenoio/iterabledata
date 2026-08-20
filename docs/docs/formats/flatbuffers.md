# FlatBuffers Format

## Description

FlatBuffers is a cross-platform serialization library developed by Google. It's designed for high performance with zero-copy reads. FlatBuffers requires schema files and generates code for reading/writing data.

## File Extensions

- `.fbs` - FlatBuffers schema files
- Binary FlatBuffers data files (no standard extension)

## Implementation Details

### Reading

The FlatBuffers implementation:
- Uses `flatbuffers` library
- Requires schema-specific generated Python code
- Reads binary FlatBuffers data
- Note: Full implementation requires generated code from schema

### Writing

Writing is not fully implemented - requires schema-specific generated code.

### Key Features

- **Schema-based**: Requires generated code from .fbs schema files
- **Zero-copy**: Can read data without deserialization
- **Fast**: High-performance serialization
- **Binary format**: Efficient binary storage
- **Cross-platform**: Works across many platforms

## Usage

```python
from iterable import open_iterable

# Note: FlatBuffers requires generated Python code from schema
# This is a simplified example
source = open_iterable('data.fbs', iterableargs={
    'schema_file': 'schema.fbs',
    'root_type': 'MyMessage'
})
```

## Parameters

- `schema_file` (str): Path to .fbs schema file
- `root_type` (str): Root type name in schema

## Limitations

1. **flatbuffers dependency**: Requires `flatbuffers` package
2. **Generated code required**: Needs Python code generated from schema
3. **Read-only (partial)**: Writing requires schema-specific implementation
4. **Schema complexity**: Complex schemas require manual code generation
5. **Binary format**: Not human-readable

## Compression Support

FlatBuffers files can be compressed with all supported codecs:
- GZip (`.fbs.gz`)
- BZip2 (`.fbs.bz2`)
- LZMA (`.fbs.xz`)
- LZ4 (`.fbs.lz4`)
- ZIP (`.fbs.zip`)
- Brotli (`.fbs.br`)
- ZStandard (`.fbs.zst`)

## Use Cases

- **High-performance systems**: When speed is critical
- **Gaming**: Game data serialization
- **Mobile apps**: Efficient data storage
- **Real-time systems**: Low-latency requirements


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Read-only**: opening with `mode="w"` raises `WriteNotSupportedError` or `ValueError`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [Protocol Buffers](protobuf.md) - Similar schema-based format
- [Cap'n Proto](capnp.md) - Another fast format
- [Thrift](thrift.md) - Apache Thrift format
