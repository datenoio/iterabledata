# Pickle Format

## Description

Pickle is Python's native serialization format. It can serialize almost any Python object to a binary format and deserialize it back. Pickle files store Python objects in a binary format that's specific to Python.

## File Extensions

- `.pickle` - Pickle files

## Implementation Details

### Reading

The Pickle implementation:
- Uses Python's built-in `pickle` module
- Reads pickled objects sequentially
- Deserializes objects to Python data structures
- Handles any Python-serializable object

### Writing

Writing support:
- Serializes Python objects to pickle format
- Writes objects sequentially
- Supports any Python-serializable object

### Key Features

- **Python-specific**: Only works with Python
- **Any object type**: Can serialize almost any Python object
- **Nested data**: Supports complex nested structures
- **Binary format**: Efficient binary storage

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('data.pickle')
for row in source:
    print(row)
source.close()

# Writing
dest = open_iterable('output.pickle', mode='w')
dest.write({'name': 'John', 'age': 30})
dest.close()
```

## Parameters

No specific parameters required.

## Limitations

1. **Python-only**: Not compatible with other languages
2. **Security risk**: Pickle can execute arbitrary code (only use trusted sources)
3. **Version compatibility**: Pickle format may change between Python versions
4. **Binary format**: Not human-readable
5. **No schema**: No schema validation or evolution

## Security Warning

⚠️ **Important**: Pickle files can execute arbitrary Python code when deserialized. Only load pickle files from trusted sources. Never load pickle files from untrusted or unknown sources.

Opening a pickle source for reading emits a `UserWarning` unless you explicitly acknowledge the risk by passing `trust=True`:

```python
from iterable import open_iterable

# Emits a UserWarning about untrusted pickle data
source = open_iterable("data.pickle")

# Explicit acknowledgement suppresses the warning
source = open_iterable("data.pickle", iterableargs={"trust": True})
```

## Compression Support

Pickle files can be compressed with all supported codecs:
- GZip (`.pickle.gz`)
- BZip2 (`.pickle.bz2`)
- LZMA (`.pickle.xz`)
- LZ4 (`.pickle.lz4`)
- ZIP (`.pickle.zip`)
- Brotli (`.pickle.br`)
- ZStandard (`.pickle.zst`)

## Use Cases

- **Python data persistence**: Saving Python objects
- **Internal data storage**: When Python-specific features are needed
- **Temporary storage**: Intermediate format in Python pipelines
- **Object serialization**: When you need to preserve Python-specific types

## Related Formats

- [JSON](json.md) - Cross-language format
- [MessagePack](msgpack.md) - Binary format with better cross-language support
