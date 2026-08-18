# WARC Format (Web Archive)

## Description

WARC (Web ARChive) is a format for storing web archive data. It's an ISO standard format used by web archiving tools to store HTTP requests, responses, metadata, and resource records. WARC files are used by the Internet Archive and other web archiving organizations.

## File Extensions

- `.warc` - WARC archive files
- `.arc` - Legacy ARC format files (alias, handled as WARC)

## Implementation Details

### Reading

The WARC implementation:
- Uses `warcio` library for reading
- Parses WARC records (request, response, metadata, etc.)
- Extracts WARC headers and content
- Converts each WARC record to a dictionary
- Supports compressed WARC files

### Writing

Writing support:
- Creates WARC files
- Writes WARC records with proper headers
- Supports different WARC record types

### Key Features

- **Web archive format**: Designed for web archiving
- **Multiple record types**: Supports request, response, metadata, resource records
- **Nested data**: Can contain complex web content
- **Compression support**: Can work with compressed WARC files
- **Standard format**: ISO standard format

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('archive.warc')
for record in source:
    print(record)  # Contains WARC record data
source.close()

# Writing
dest = open_iterable('output.warc', mode='w')
dest.write({
    'record_type': 'response',
    'target_uri': 'http://example.com',
    'content': b'...'  # Binary content
})
dest.close()
```

## Parameters

No specific parameters required.

## Limitations

1. **warcio dependency**: Requires `warcio` package
2. **Binary format**: Contains binary content
3. **Complex structure**: WARC records can be complex
4. **No totals**: Totals counting not supported (requires full iteration)
5. **Memory usage**: Large WARC files may use significant memory

## Compression Support

WARC files can be compressed with all supported codecs:
- GZip (`.warc.gz`)
- BZip2 (`.warc.bz2`)
- LZMA (`.warc.xz`)
- LZ4 (`.warc.lz4`)
- ZIP (`.warc.zip`)
- Brotli (`.warc.br`)
- ZStandard (`.warc.zst`)

Note: WARC files often use internal compression as well.

## Use Cases

- **Web archiving**: Archiving web content
- **Historical preservation**: Preserving web history
- **Research**: Web research and analysis
- **Compliance**: Meeting web archiving requirements

## Related Formats

- [CDX](cdx.md) - WARC index format
- [ARC](warc.md) - Legacy archive format (handled as WARC)
