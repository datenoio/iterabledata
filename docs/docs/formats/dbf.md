# DBF Format

## Description

DBF (dBase/FoxPro) is a database file format used by dBase, FoxPro, and other database systems. It's a binary format for storing tabular data with a header containing field definitions and records stored sequentially.

## File Extensions

- `.dbf` - dBase/FoxPro database files

## Implementation Details

### Reading

The DBF implementation:
- Uses `dbfread` library for reading
- Supports various encodings
- Reads records sequentially
- Converts records to dictionaries
- Handles field types appropriately

### Writing

Writing is not currently supported for DBF format.

### Key Features

- **Field types**: Supports various field types (character, numeric, date, etc.)
- **Encoding support**: Handles various character encodings
- **Totals support**: Can count total records
- **Legacy format**: Works with old database files

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.dbf') as source:
    for row in source:
        print(row)

# With specific encoding
source = open_iterable('data.dbf', iterableargs={
    'encoding': 'cp1251'  # Windows-1251 encoding
})
```

## Parameters

- `encoding` (str): Character encoding (default: `utf-8`)

## Limitations

1. **Read-only**: DBF format does not support writing
2. **dbfread dependency**: Requires `dbfread` package
3. **File path required**: Requires filename, not stream
4. **Flat data only**: Only supports tabular data
5. **Legacy format**: Older database format
6. **Encoding issues**: May require specific encoding for non-ASCII data

## Compression Support

DBF files can be compressed with all supported codecs:
- GZip (`.dbf.gz`)
- BZip2 (`.dbf.bz2`)
- LZMA (`.dbf.xz`)
- LZ4 (`.dbf.lz4`)
- ZIP (`.dbf.zip`)
- Brotli (`.dbf.br`)
- ZStandard (`.dbf.zst`)

## Use Cases

- **Legacy data**: Reading old database files
- **Data migration**: Converting from dBase/FoxPro
- **Government data**: Some government datasets use DBF format
- **GIS data**: Shapefile format includes DBF files


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Read-only**: opening with `mode="w"` raises `WriteNotSupportedError` or `ValueError`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [CSV](csv.md) - Simple text format
- [SQLite](sqlite.md) - Modern database format
