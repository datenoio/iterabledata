# XLSX Format (Excel 2007+)

## Description

XLSX is the modern XML-based file format used by Microsoft Excel 2007 and later. It's an open standard (ECMA-376, ISO/IEC 29500) that stores spreadsheet data including formulas, formatting, and multiple sheets.

## File Extensions

- `.xlsx` - Excel 2007+ files

## Implementation Details

### Reading

The XLSX implementation:
- Uses `openpyxl` with `read_only=True` so large workbooks stream row by row
- Supports multiple sheets (by index or name)
- Extracts column headers from the first non-blank row (if not specified)
- Converts each row to a dictionary

### Writing

Writing is **not supported**. Attempting to write raises `WriteNotSupportedError`. Convert to [CSV](csv.md) or [Parquet](parquet.md) when you need an output file.

### Key Features

- **Multiple sheets**: Read a sheet by index or name
- **Header detection**: Automatically extracts headers from the first non-blank row
- **Efficient iteration**: Uses row iterators for large files
- **Totals support**: Can count total rows
- **Read-only**: No XLSX writer in this release

## Usage

```python
from iterable import open_iterable
from iterable.datatypes.xlsx import XLSXIterable

# First sheet, headers from the first non-blank row
with open_iterable("data.xlsx") as source:
    for row in source:
        print(row)

# Sheet by index (0-based) or name
with open_iterable("data.xlsx", iterableargs={"page": 1}) as source:
    for row in source:
        print(row)

with open_iterable("data.xlsx", iterableargs={"page": "Sheet2"}) as source:
    for row in source:
        print(row)

sheets = XLSXIterable("data.xlsx").list_tables("data.xlsx")
for sheet_name in sheets:
    with open_iterable("data.xlsx", iterableargs={"page": sheet_name}) as source:
        for row in source:
            process(row)
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `page` | int or str | `0` | No | Sheet index (int, 0-indexed) or name (str). |
| `keys` | list[str] | auto-detected | No | Column names. Extracted from the first non-blank row if omitted. |
| `start_line` | int | `0` | No | Row number to start reading from (0-indexed). |

## Error Handling

```python
from iterable import open_iterable
from iterable.datatypes.xlsx import XLSXIterable

try:
    with open_iterable("data.xlsx", iterableargs={"page": 0}) as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("XLSX file not found")
except ValueError as e:
    print(f"Invalid sheet: {e}")
    print("Available sheets:", XLSXIterable("data.xlsx").list_tables("data.xlsx"))
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install iterabledata[excel]")
```

### Common Errors

- **ValueError**: Invalid sheet index or name — use `list_tables()` first
- **ImportError**: Missing `openpyxl` — `pip install iterabledata[excel]`
- **FileNotFoundError**: Path is wrong or the file is missing
- **WriteNotSupportedError**: Writing XLSX is not implemented

## Limitations

1. **openpyxl dependency**: Requires the `excel` extra
2. **Flat data only**: Tabular sheets only
3. **File path required**: Filename, not a stream
4. **Read-only**: No writer
5. **Formulas**: Values are read; formulas are not evaluated

## Compression Support

XLSX files are ZIP archives internally. Additional codecs still work (`.xlsx.gz`, `.xlsx.zst`, and so on) but rarely help.

## Use Cases

- **Data analysis**: Reading Excel exports
- **Data migration**: Spreadsheet to CSV/Parquet/JSONL
- **Business data**: Multi-sheet workbooks

## Related Formats

- [XLS](xls.md) - Legacy Excel format (read-only)
- [XLSB](xlsb.md) - Excel binary workbooks (read-only)
- [ODS](ods.md) - OpenDocument Spreadsheet (read-only)
- [CSV](csv.md) - Writable tabular text
