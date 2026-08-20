# BSON Format

## Description

BSON (Binary JSON) is a binary-encoded serialization of JSON-like documents. It's used by MongoDB for data storage and network transfer. BSON extends JSON with additional data types like Date and Binary, and stores data more efficiently than JSON.

## File Extensions

- `.bson` - BSON files

## Implementation Details

### Reading

The BSON implementation:
- Uses `bson` library for decoding
- Reads BSON documents sequentially from file
- Converts BSON documents to Python dictionaries
- Handles BSON-specific types (Date, Binary, etc.)

### Writing

Writing support:
- Encodes Python dictionaries to BSON
- Writes BSON documents sequentially
- Handles BSON-specific types

### Key Features

- **Binary format**: More efficient than JSON
- **Extended types**: Supports Date, Binary, and other types
- **Nested data**: Supports complex nested structures
- **MongoDB compatible**: Works with MongoDB data

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.bson') as source:
    for row in source:
        print(row)

# Writing
with open_iterable('output.bson', mode='w') as dest:
    dest.write({'name': 'John', 'age': 30})
```

## Parameters

No specific parameters required.

## Limitations

1. **bson dependency**: Requires `bson` package
2. **Binary format**: Not human-readable
3. **Type conversion**: Some BSON types may be converted to Python equivalents
4. **File format**: Expects sequential BSON documents (not MongoDB dump format)

## Compression Support

BSON files can be compressed with all supported codecs:
- GZip (`.bson.gz`)
- BZip2 (`.bson.bz2`)
- LZMA (`.bson.xz`)
- LZ4 (`.bson.lz4`)
- ZIP (`.bson.zip`)
- Brotli (`.bson.br`)
- ZStandard (`.bson.zst`)

## Use Cases

- **MongoDB data**: Exporting/importing MongoDB collections
- **Binary JSON**: When JSON is too verbose
- **Data transfer**: Efficient binary data exchange
- **Type preservation**: When you need to preserve specific data types

## Related Formats

- [JSON](json.md) - Text-based JSON format
- [JSONL](jsonl.md) - Line-delimited JSON
- [MessagePack](msgpack.md) - Another binary JSON format
