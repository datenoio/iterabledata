# RecordIO Format (Google)

## Description

RecordIO is a binary file format developed by Google for storing sequences of records. Each record is prefixed with its length and a CRC32 checksum. RecordIO is used in various Google systems and provides efficient sequential reading of records.

## File Extensions

- `.rio` - RecordIO files
- `.recordio` - RecordIO files (alias)

## Implementation Details

### Reading

The RecordIO implementation:
- Parses RecordIO format
- Reads length-prefixed records with CRC32 checksums
- Handles binary record data
- Converts records to dictionaries
- Supports streaming for large files

### Writing

Writing support:
- Writes length-prefixed JSON records with CRC32 checksums
- Same framing as the reader

### Key Features

- **Google format**: Developed by Google
- **CRC32 checksums**: Includes data integrity checks
- **Length-prefixed**: Records prefixed with length
- **Nested data**: Supports complex data structures
- **Streaming**: Processes files record by record

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.rio', iterableargs={
    'value_key': 'value'
}) as source:
    for record in source:
        print(record)  # Contains record data

# Writing
with open_iterable('output.rio', mode='w') as dest:
    dest.write({'id': 1, 'payload': 'hello'})
```

## Parameters

- `value_key` (str): Key name for record value (default: `value`)

## Limitations

1. **Binary format**: Not human-readable
2. **CRC32 validation**: Simplified CRC32 implementation
3. **Format complexity**: RecordIO format can be complex
4. **Google-specific**: Primarily used in Google systems

## Compression Support

RecordIO files can be compressed with all supported codecs:
- GZip (`.rio.gz`)
- BZip2 (`.rio.bz2`)
- LZMA (`.rio.xz`)
- LZ4 (`.rio.lz4`)
- ZIP (`.rio.zip`)
- Brotli (`.rio.br`)
- ZStandard (`.rio.zst`)

## Use Cases

- **Google systems**: Working with Google data formats
- **Data storage**: Efficient record storage
- **Data pipelines**: Processing RecordIO data
- **Sequential reading**: When you need sequential record access

## Related Formats

- [TFRecord](tfrecord.md) - Similar TensorFlow format
- [SequenceFile](sequencefile.md) - Hadoop format
