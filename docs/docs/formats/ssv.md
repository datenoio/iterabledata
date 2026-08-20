# SSV Format (Semicolon-Separated Values)

## Description

SSV (Semicolon-Separated Values) is a variant of CSV where fields are separated by semicolons (`;`). It's commonly used in European locales where comma is used as decimal separator. SSV extends the CSV implementation with a fixed semicolon delimiter.

## File Extensions

- `.ssv` - Semicolon-separated values files

## Implementation Details

### Reading

The SSV implementation:
- Extends CSV implementation
- Uses semicolon (`;`) as delimiter
- Supports all CSV features (encoding detection, quote handling)
- Converts each row to a dictionary

### Writing

Writing support:
- Uses semicolon delimiter
- Supports all CSV writing features
- Requires field names specification

### Key Features

- **Semicolon delimiter**: Fixed semicolon character separator
- **CSV compatibility**: Inherits all CSV features
- **Encoding support**: Automatic encoding detection
- **Quote handling**: Properly handles quoted fields
- **Totals support**: Can count total rows

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.ssv') as source:
    for row in source:
        print(row)

# Writing
with open_iterable('output.ssv', mode='w', iterableargs={
    'keys': ['id', 'name', 'value']
}) as dest:
    dest.write({'id': '1', 'name': 'John', 'value': 'test'})
```

## Parameters

- `keys` (list[str]): Column names (required for writing)
- `encoding` (str): File encoding (default: auto-detected)
- `quotechar` (str): Quote character (default: `"`)

## Limitations

1. **Flat data only**: Only supports tabular data
2. **Schema required for writing**: Must specify field names
3. **No type preservation**: All values are strings
4. **Semicolon in data**: If data contains semicolons, they must be quoted

## Compression Support

SSV files can be compressed with all supported codecs:
- GZip (`.ssv.gz`)
- BZip2 (`.ssv.bz2`)
- LZMA (`.ssv.xz`)
- LZ4 (`.ssv.lz4`)
- ZIP (`.ssv.zip`)
- Brotli (`.ssv.br`)
- ZStandard (`.ssv.zst`)

## Use Cases

- **European locales**: When comma is used as decimal separator
- **Excel exports**: Some Excel exports use semicolon delimiter
- **Regional formats**: Common in European data formats


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [CSV](csv.md) - Comma-separated format
- [PSV](psv.md) - Pipe-separated format
- [TSV](csv.md) - Tab-separated format (uses CSV with tab delimiter)
