# CBOR Format

## Description

CBOR (Concise Binary Object Representation) is a binary data format inspired by JSON. It's designed to be more compact and efficient than JSON while maintaining similar data structures. CBOR is an IETF standard (RFC 7049).

## File Extensions

- `.cbor` - CBOR files

## Implementation Details

### Reading

The CBOR implementation:
- Uses `cbor2` or `cbor` library for decoding
- Supports reading single objects or arrays
- Converts CBOR data to Python objects
- Handles nested structures

### Writing

Writing support:
- Encodes Python objects to CBOR format
- Writes binary CBOR data
- Supports nested structures

### Key Features

- **Binary format**: More compact than JSON
- **JSON-like**: Similar data structures to JSON
- **Nested data**: Supports complex nested structures
- **Type preservation**: Maintains data types
- **Standard format**: IETF standard (RFC 7049)

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('data.cbor')
for row in source:
    print(row)
source.close()

# Writing
dest = open_iterable('output.cbor', mode='w')
dest.write({'name': 'John', 'age': 30})
dest.close()
```

## Parameters

No specific parameters required.

## Limitations

1. **Dependency**: Requires `cbor2` or `cbor` package
2. **Binary format**: Not human-readable
3. **File structure**: Expects single object or array of objects
4. **Memory usage**: Entire file may be loaded into memory

## Compression Support

CBOR files can be compressed with all supported codecs:
- GZip (`.cbor.gz`)
- BZip2 (`.cbor.bz2`)
- LZMA (`.cbor.xz`)
- LZ4 (`.cbor.lz4`)
- ZIP (`.cbor.zip`)
- Brotli (`.cbor.br`)
- ZStandard (`.cbor.zst`)

## Use Cases

- **IoT devices**: Efficient data exchange for IoT
- **APIs**: Compact API responses
- **Data storage**: Efficient binary storage
- **Embedded systems**: Resource-constrained environments

## Related Formats

- [JSON](json.md) - Text-based format
- [MessagePack](msgpack.md) - Similar binary format
- [UBJSON](ubjson.md) - Another binary JSON format
