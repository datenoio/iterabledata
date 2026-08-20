# UBJSON Format

## Description

UBJSON (Universal Binary JSON) is a binary JSON format that's a drop-in replacement for JSON. It provides the same data structures as JSON but in a more efficient binary format. UBJSON is designed to be faster and more compact than JSON.

## File Extensions

- `.ubj` - UBJSON files
- `.ubjson` - UBJSON files (alias)

## Implementation Details

### Reading

The UBJSON implementation:
- Uses `py-ubjson` library for decoding
- Reads entire file into memory
- Supports arrays and single objects
- Converts UBJSON data to Python objects

### Writing

Writing support:
- Encodes Python objects to UBJSON format
- Writes binary UBJSON data
- Supports nested structures

### Key Features

- **Binary format**: More efficient than JSON
- **JSON-compatible**: Same data structures as JSON
- **Nested data**: Supports complex nested structures
- **Type preservation**: Maintains data types

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.ubj') as source:
    for row in source:
        print(row)

# Writing
with open_iterable('output.ubj', mode='w') as dest:
    dest.write({'name': 'John', 'age': 30})
```

## Parameters

No specific parameters required.

## Limitations

1. **py-ubjson dependency**: Requires `py-ubjson` package
2. **Binary format**: Not human-readable
3. **Memory usage**: Entire file is loaded into memory
4. **File structure**: Expects single object or array of objects

## Compression Support

UBJSON files can be compressed with all supported codecs:
- GZip (`.ubj.gz`)
- BZip2 (`.ubj.bz2`)
- LZMA (`.ubj.xz`)
- LZ4 (`.ubj.lz4`)
- ZIP (`.ubj.zip`)
- Brotli (`.ubj.br`)
- ZStandard (`.ubj.zst`)

## Use Cases

- **High-performance APIs**: When JSON is too slow
- **Data storage**: Efficient binary storage
- **Real-time systems**: Low-latency data exchange
- **Gaming**: Fast data serialization

## Related Formats

- [JSON](json.md) - Text-based format
- [MessagePack](msgpack.md) - Similar binary format
- [CBOR](cbor.md) - Another binary format
