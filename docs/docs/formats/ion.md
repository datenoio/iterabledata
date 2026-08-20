# Ion Format

## Description

Ion is a richly-typed, self-describing, hierarchical data serialization format. It was developed by Amazon and is used in Amazon's services. Ion supports a superset of JSON data types plus additional types like timestamps, decimals, and symbols.

## File Extensions

- `.ion` - Ion files

## Implementation Details

### Reading

The Ion implementation:
- Uses `ion-python` library for reading
- Reads Ion data from binary stream
- Converts Ion values to Python dictionaries
- Handles arrays, structs, and single values

### Writing

Writing support:
- Serializes Python dictionaries to Ion format
- Writes Ion binary data
- Supports nested structures

### Key Features

- **Rich types**: Supports more types than JSON
- **Self-describing**: Type information embedded in data
- **Hierarchical**: Supports complex nested structures
- **Amazon format**: Used in Amazon services

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.ion') as source:
    for row in source:
        print(row)

# Writing
with open_iterable('output.ion', mode='w') as dest:
    dest.write({'name': 'John', 'age': 30})
```

## Parameters

No specific parameters required.

## Limitations

1. **Ion extra**: Requires `pip install iterabledata[ion]` (`ion-python`)
2. **Binary format**: Not human-readable
3. **Memory usage**: Entire file may be loaded into memory
4. **Less common**: Not as widely used as JSON or other formats

## Compression Support

Ion files can be compressed with all supported codecs:
- GZip (`.ion.gz`)
- BZip2 (`.ion.bz2`)
- LZMA (`.ion.xz`)
- LZ4 (`.ion.lz4`)
- ZIP (`.ion.zip`)
- Brotli (`.ion.br`)
- ZStandard (`.ion.zst`)

## Use Cases

- **Amazon services**: Working with Amazon data formats
- **Rich data types**: When you need more types than JSON
- **Self-describing data**: When type information is important

## Related Formats

- [JSON](json.md) - Simpler format
- [CBOR](cbor.md) - Another binary format
- [MessagePack](msgpack.md) - Similar binary format
