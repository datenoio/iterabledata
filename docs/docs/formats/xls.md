# XLS Format (Excel 97-2003)

## Description

XLS is the binary file format used by Microsoft Excel versions 97-2003. It's a proprietary format for storing spreadsheet data including formulas, formatting, and multiple sheets.

## File Extensions

- `.xls` - Excel 97-2003 files

## Implementation Details

### Reading

The XLS implementation:
- Uses `xlrd` library for reading
- Supports multiple sheets (pages)
- Extracts column headers from first row (if not specified)
- Handles dates and numbers appropriately
- Converts each row to a dictionary

### Writing

Writing is **not supported**. Convert to [CSV](csv.md) or [Parquet](parquet.md) for output. XLSX is also read-only.

### Key Features

- **Multiple sheets**: Can read from specific sheet by index
- **Header detection**: Automatically extracts headers from first row
- **Date handling**: Properly converts Excel dates
- **Type handling**: Converts numbers and dates appropriately
- **Totals support**: Can count total rows

## Usage

```python
from iterable import open_iterable

# Basic reading (first sheet, headers from first row)
with open_iterable('data.xls') as source:
    for row in source:
        print(row)

# Read specific sheet
source = open_iterable('data.xls', iterableargs={
    'page': 1  # Second sheet (0-indexed)
})

# List available sheets
from iterable.datatypes.xls import XLSIterable

# Discover sheets before opening
sheets = XLSIterable('data.xls').list_tables('data.xls')
print(f"Available sheets: {sheets}")

# List sheets after opening (reuses workbook)
with open_iterable('data.xls', iterableargs={'page': 0}) as source:
    all_sheets = source.list_tables()  # Reuses open workbook
    print(f"All sheets: {all_sheets}")

# Specify column names manually
source = open_iterable('data.xls', iterableargs={
    'keys': ['id', 'name', 'date'],
    'start_line': 0  # Start from first row
})
```

## Parameters

- `page` (int): Sheet index to read (default: `0`)
- `keys` (list[str]): Column names (default: extracted from first row)
- `start_line` (int): Row to start reading from (default: `0`)

## Limitations

1. **Read-only**: XLS format does not support writing (use XLSX)
2. **xlrd dependency**: Requires `xlrd` package
3. **Legacy format**: Older Excel format (use XLSX for new files)
4. **Flat data only**: Only supports tabular data
5. **Limited features**: Some Excel features may not be fully supported
6. **File path required**: Requires filename, not stream

## Compression Support

XLS files can be compressed with all supported codecs:
- GZip (`.xls.gz`)
- BZip2 (`.xls.bz2`)
- LZMA (`.xls.xz`)
- LZ4 (`.xls.lz4`)
- ZIP (`.xls.zip`)
- Brotli (`.xls.br`)
- ZStandard (`.xls.zst`)

## Use Cases

- **Legacy data**: Reading old Excel files
- **Data migration**: Converting from Excel to other formats
- **Data analysis**: Processing Excel data
- **Reporting**: Reading Excel reports


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Read-only**: opening with `mode="w"` raises `WriteNotSupportedError` or `ValueError`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [XLSX](xlsx.md) - Modern Excel format (supports writing)
- [ODS](ods.md) - OpenDocument Spreadsheet format
- [CSV](csv.md) - Simple text format
