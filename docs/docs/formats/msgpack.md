# MessagePack Format

## Description

MessagePack is an efficient binary serialization format that's like JSON but faster and more compact. It's designed for efficient data exchange between systems and is widely used in distributed systems and APIs.

## File Extensions

- `.msgpack` - MessagePack files
- `.mp` - MessagePack files (alias)

## Implementation Details

### Reading

The MessagePack implementation:
- Uses `msgpack` library for unpacking
- Reads MessagePack data sequentially
- Converts MessagePack data to Python objects
- Supports streaming for large files

### Writing

Writing support:
- Packs Python objects to MessagePack format
- Writes binary data sequentially
- Handles nested structures

### Key Features

- **Binary format**: More compact than JSON
- **Fast serialization**: Optimized for speed
- **Nested data**: Supports complex nested structures
- **Type preservation**: Maintains data types
- **Streaming**: Can process large files efficiently

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('data.msgpack')
for row in source:
    print(row)
source.close()

# Writing
dest = open_iterable('output.msgpack', mode='w')
dest.write({'name': 'John', 'age': 30})
dest.close()
```

## Parameters

No specific parameters required.

## Limitations

1. **msgpack dependency**: Requires `msgpack` package
2. **Binary format**: Not human-readable
3. **File structure**: Expects sequential MessagePack objects
4. **Type limitations**: Some Python types may not serialize perfectly

## Compression Support

MessagePack files can be compressed with all supported codecs:
- GZip (`.msgpack.gz`)
- BZip2 (`.msgpack.bz2`)
- LZMA (`.msgpack.xz`)
- LZ4 (`.msgpack.lz4`)
- ZIP (`.msgpack.zip`)
- Brotli (`.msgpack.br`)
- ZStandard (`.msgpack.zst`)

## Use Cases

- **API communication**: Efficient data exchange
- **Distributed systems**: Fast serialization for microservices
- **Caching**: Compact storage format
- **Data pipelines**: Efficient intermediate format

## Related Formats

- [JSON](json.md) - Text-based format
- [BSON](bson.md) - MongoDB's binary format
- [CBOR](cbor.md) - Another binary format
