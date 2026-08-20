# FlexBuffers Format

## Description

FlexBuffers is a schemaless binary serialization format developed by Google as part of FlatBuffers. Unlike FlatBuffers, FlexBuffers doesn't require a schema and is more flexible. It's designed for cases where you need a flexible, schemaless binary format.

## File Extensions

- `.flexbuf` - FlexBuffers files
- `.flexbuffers` - FlexBuffers files (alias)

## Implementation Details

### Reading

The FlexBuffers implementation:
- Imports `flexbuffers` when installed (there is no PyPI extra; see Limitations)
- Reads binary FlexBuffers data
- Supports single documents or arrays
- Converts FlexBuffers data to Python objects

### Writing

Writing support:
- Encodes Python objects to FlexBuffers format
- Writes binary FlexBuffers data
- Supports nested structures

### Key Features

- **Schemaless**: No schema required
- **Binary format**: Efficient binary serialization
- **Flexible**: More flexible than FlatBuffers
- **Nested data**: Supports complex nested structures
- **Type preservation**: Maintains data types

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.flexbuf') as source:
    for row in source:
        print(row)

# Writing
with open_iterable('output.flexbuf', mode='w') as dest:
    dest.write({'name': 'John', 'age': 30})
```

## Parameters

No specific parameters required.

## Limitations

1. **Not on PyPI**: There is no `iterabledata` extra for FlexBuffers. The reader imports `flexbuffers`, which is not a pip-installable package today.
2. **Binary format**: Not human-readable
3. **Memory usage**: Entire file may be loaded into memory
4. **Less common**: Not as widely used as other formats

## Compression Support

FlexBuffers files can be compressed with all supported codecs:
- GZip (`.flexbuf.gz`)
- BZip2 (`.flexbuf.bz2`)
- LZMA (`.flexbuf.xz`)
- LZ4 (`.flexbuf.lz4`)
- ZIP (`.flexbuf.zip`)
- Brotli (`.flexbuf.br`)
- ZStandard (`.flexbuf.zst`)

## Use Cases

- **Schemaless binary**: When you need schemaless binary format
- **Flexible serialization**: Dynamic data structures
- **Game development**: Game data serialization

## Related Formats

- [FlatBuffers](flatbuffers.md) - Schema-based version
- [MessagePack](msgpack.md) - Similar schemaless format
- [CBOR](cbor.md) - Another binary format
