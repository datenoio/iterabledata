# SMILE Format

## Description

SMILE (Smile is a Machine-Interchangeable Language for Everything) is a binary data format similar to JSON but more compact. It was developed by the Jackson JSON library team and provides efficient binary serialization of JSON-like data structures.

## File Extensions

- `.smile` - SMILE format files

## Implementation Details

### Reading

The SMILE implementation:
- Imports `smile` when installed (there is no PyPI extra; see Limitations)
- Reads binary SMILE data
- Supports single documents or arrays
- Converts SMILE data to Python objects

### Writing

Writing support:
- Encodes Python objects to SMILE format
- Writes binary SMILE data
- Supports nested structures

### Key Features

- **Binary format**: More compact than JSON
- **JSON-compatible**: Same data structures as JSON
- **Nested data**: Supports complex nested structures
- **Type preservation**: Maintains data types

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.smile') as source:
    for row in source:
        print(row)

# Writing
with open_iterable('output.smile', mode='w') as dest:
    dest.write({'name': 'John', 'age': 30})
```

## Parameters

No specific parameters required.

## Limitations

1. **Not on PyPI**: There is no `iterabledata` extra for SMILE. The reader imports `smile` and the ImportError names `smile-json`, which is not a pip-installable package today.
2. **Binary format**: Not human-readable
3. **Memory usage**: Entire file may be loaded into memory
4. **Less common**: Not as widely used as JSON or MessagePack

## Compression Support

SMILE files can be compressed with all supported codecs:
- GZip (`.smile.gz`)
- BZip2 (`.smile.bz2`)
- LZMA (`.smile.xz`)
- LZ4 (`.smile.lz4`)
- ZIP (`.smile.zip`)
- Brotli (`.smile.br`)
- ZStandard (`.smile.zst`)

## Use Cases

- **Binary JSON**: When JSON is too verbose
- **Data storage**: Efficient binary storage
- **Jackson integration**: Working with Jackson-based systems

## Related Formats

- [JSON](json.md) - Text-based format
- [MessagePack](msgpack.md) - Similar binary format
- [CBOR](cbor.md) - Another binary format
