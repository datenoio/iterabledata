# SequenceFile Format (Hadoop)

## Description

SequenceFile is a flat file format used by Apache Hadoop for storing key-value pairs. It's a binary format designed for efficient storage and retrieval in Hadoop. SequenceFile supports compression and is commonly used in Hadoop MapReduce jobs.

## File Extensions

- `.seq` - SequenceFile files
- `.sequencefile` - SequenceFile files (alias)

## Implementation Details

### Reading

The SequenceFile implementation:
- Parses SequenceFile format
- Reads file header with metadata
- Extracts key-value pairs
- Handles sync markers
- Converts records to dictionaries

### Writing

Writing support:
- Writes Hadoop-style key/value records from `key` / `value` fields
- Nested values are JSON-encoded

### Key Features

- **Hadoop format**: Designed for Hadoop
- **Key-value pairs**: Stores key-value data
- **Sync markers**: Supports random access
- **Compression**: Supports compression
- **Nested data**: Supports complex data structures

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.seq', iterableargs={
    'key_name': 'key',
    'value_name': 'value'
}) as source:
    for record in source:
        print(record)  # Contains key and value

# Writing
with open_iterable('output.seq', mode='w') as dest:
    dest.write({'key': 'k1', 'value': {'n': 1}})
```

## Parameters

- `key_name` (str): Key name for record key (default: `key`)
- `value_name` (str): Key name for record value (default: `value`)

## Limitations

1. **Binary format**: Not human-readable
2. **Hadoop-specific**: Designed for Hadoop
3. **Format complexity**: SequenceFile format can be complex
4. **Simplified implementation**: May not support all SequenceFile features

## Compression Support

SequenceFile has built-in compression support (separate from file-level compression):
- None, Record, Block compression

SequenceFile files can also be compressed with file-level codecs:
- GZip (`.seq.gz`)
- BZip2 (`.seq.bz2`)
- LZMA (`.seq.xz`)
- LZ4 (`.seq.lz4`)
- ZIP (`.seq.zip`)
- Brotli (`.seq.br`)
- ZStandard (`.seq.zst`)

## Use Cases

- **Hadoop processing**: Processing Hadoop data
- **MapReduce**: MapReduce job data
- **Data storage**: Storing data in Hadoop
- **Big data**: Large-scale data processing


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [Avro](avro.md) - Another Hadoop format
- [Parquet](parquet.md) - Columnar format for Hadoop
