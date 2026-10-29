# SequenceFile Format (Hadoop)

## Description

SequenceFile is a flat file format used by Apache Hadoop for storing key-value pairs. It's a binary format designed for efficient storage and retrieval in Hadoop. SequenceFile supports compression and is commonly used in Hadoop MapReduce jobs.

## File Extensions

- `.seq` - SequenceFile files
- `.sequencefile` - SequenceFile files (alias)

## Implementation Details

### Reading

The SequenceFile implementation:
- Parses the Hadoop header (`SEQ` magic, versions 4-6): key/value class names, compression flags, metadata and sync marker
- Extracts key-value pairs and verifies sync markers between records
- Decodes `Text`, `BytesWritable`, `IntWritable`, `LongWritable` and `NullWritable` keys and values; other classes are decoded from their raw bytes
- Parses text payloads as JSON when possible, otherwise returns them as strings (non-UTF-8 bytes as base64)
- Converts records to dictionaries
- Reads files without the `SEQ` magic as the headerless `[key length][value length][key][value]` layout that earlier iterabledata releases wrote

### Writing

Writing support:
- Writes uncompressed Hadoop SequenceFile version 6 files: header, then `[record length][key length][key][value]` records with `org.apache.hadoop.io.Text` keys and values
- Writes a sync marker every 100 KB, like Hadoop
- Takes key and value from the `key` / `value` fields (or `key_name` / `value_name`); a record with other fields is written as the value
- Nested values are JSON-encoded; values without a JSON type use the [shared value encoding](jsonl.md#value-encoding-when-writing)
- A file written with no records still holds a valid header, so it reads back as empty

### Key Features

- **Hadoop format**: Designed for Hadoop
- **Key-value pairs**: Stores key-value data
- **Sync markers**: Supports random access
- **Compression**: File-level codecs (`.seq.gz`, `.seq.zst`, ...); built-in record/block compression is not supported
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
4. **No built-in compression**: record- and block-compressed SequenceFiles raise `FormatParseError`; versions older than 4 are not supported
5. **Text output only**: written keys and values are always `org.apache.hadoop.io.Text`

## Compression Support

The SequenceFile format defines built-in compression (separate from file-level compression):
- None, Record, Block compression

Only uncompressed SequenceFiles are read and written. SequenceFile files can be compressed with file-level codecs:
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
- **Bad or unsupported input**: a truncated or malformed header or record, an unsupported version, built-in compression or a sync marker that does not match the header raise `FormatParseError` (a `ValueError` subclass) with the row number where the record failed; rows read before it are kept.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [Avro](avro.md) - Another Hadoop format
- [Parquet](parquet.md) - Columnar format for Hadoop
