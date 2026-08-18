# PSV Format (Pipe-Separated Values)

## Description

PSV (Pipe-Separated Values) is a variant of CSV where fields are separated by pipe characters (`|`). It's useful when data contains commas that shouldn't be treated as delimiters. PSV extends the CSV implementation with a fixed pipe delimiter.

## File Extensions

- `.psv` - Pipe-separated values files

## Implementation Details

### Reading

The PSV implementation:
- Extends CSV implementation
- Uses pipe (`|`) as delimiter
- Supports all CSV features (encoding detection, quote handling)
- Converts each row to a dictionary

### Writing

Writing support:
- Uses pipe delimiter
- Supports all CSV writing features
- Requires field names specification

### Key Features

- **Pipe delimiter**: Fixed pipe character separator
- **CSV compatibility**: Inherits all CSV features
- **Encoding support**: Automatic encoding detection
- **Quote handling**: Properly handles quoted fields
- **Totals support**: Can count total rows

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('data.psv')
for row in source:
    print(row)
source.close()

# Writing
dest = open_iterable('output.psv', mode='w', iterableargs={
    'keys': ['id', 'name', 'value']
})
dest.write({'id': '1', 'name': 'John', 'value': 'test'})
dest.close()
```

## Parameters

- `keys` (list[str]): Column names (required for writing)
- `encoding` (str): File encoding (default: auto-detected)
- `quotechar` (str): Quote character (default: `"`)

## Limitations

1. **Flat data only**: Only supports tabular data
2. **Schema required for writing**: Must specify field names
3. **No type preservation**: All values are strings
4. **Pipe in data**: If data contains pipe characters, they must be quoted

## Compression Support

PSV files can be compressed with all supported codecs:
- GZip (`.psv.gz`)
- BZip2 (`.psv.bz2`)
- LZMA (`.psv.xz`)
- LZ4 (`.psv.lz4`)
- ZIP (`.psv.zip`)
- Brotli (`.psv.br`)
- ZStandard (`.psv.zst`)

## Use Cases

- **Data with commas**: When data contains commas that shouldn't be delimiters
- **Unix pipelines**: Compatible with Unix pipe operations
- **Database exports**: Some databases export in PSV format

## Related Formats

- [CSV](csv.md) - Comma-separated format
- [SSV](ssv.md) - Semicolon-separated format
- [TSV](csv.md) - Tab-separated format (uses CSV with tab delimiter)
