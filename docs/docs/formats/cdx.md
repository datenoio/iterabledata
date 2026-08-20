# CDX Format (Capture Index)

## Description

CDX (Capture inDeX) is a text format used for indexing web archive files (WARC/ARC). CDX files contain metadata about archived web resources, including URLs, timestamps, MIME types, HTTP response codes, and pointers to the actual archived content.

## File Extensions

- `.cdx` - CDX index files

## Implementation Details

### Reading

The CDX implementation:
- Parses space-separated CDX format
- Handles quoted fields containing spaces
- Extracts standard CDX fields (URL, timestamp, MIME type, etc.)
- Converts each line to a dictionary
- Supports custom field names

### Writing

Writing is not currently supported for CDX format.

### Key Features

- **Space-separated**: Uses spaces as delimiters
- **Quoted fields**: Handles quoted fields with spaces
- **Web archive index**: Designed for web archive indexing
- **Totals support**: Can count total index entries
- **WARC integration**: Works with WARC files

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('index.cdx') as source:
    for row in source:
        print(row)  # Contains: url, timestamp, mime_type, status_code, etc.

# With custom field names
source = open_iterable('index.cdx', iterableargs={
    'keys': ['url', 'timestamp', 'original_url', 'mime_type', 'status_code']
})
```

## Parameters

- `keys` (list[str]): Field names (default: standard CDX-11 format fields)
- `encoding` (str): File encoding (default: `utf8`)

## Standard CDX Fields

CDX-11 format includes:
- `url`, `timestamp`, `original_url`, `mime_type`, `status_code`, `checksum`, `redirect`, `filename`, `offset`

## Limitations

1. **Read-only**: CDX format does not support writing
2. **Format-specific**: Must follow CDX format specification
3. **Space-separated**: Spaces in data must be quoted
4. **Flat data only**: Only supports tabular index data

## Compression Support

CDX files can be compressed with all supported codecs:
- GZip (`.cdx.gz`)
- BZip2 (`.cdx.bz2`)
- LZMA (`.cdx.xz`)
- LZ4 (`.cdx.lz4`)
- ZIP (`.cdx.zip`)
- Brotli (`.cdx.br`)
- ZStandard (`.cdx.zst`)

## Use Cases

- **Web archiving**: Indexing web archive files
- **Archive search**: Searching archived web content
- **WARC integration**: Working with WARC archive files
- **Historical data**: Accessing historical web data

## Related Formats

- [WARC](warc.md) - Web archive format
- [ARC](warc.md) - Legacy web archive format (alias for WARC)
