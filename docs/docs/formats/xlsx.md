# XLSX Format (Excel 2007+)

## Description

XLSX is the modern XML-based file format used by Microsoft Excel 2007 and later. It's an open standard (ECMA-376, ISO/IEC 29500) that stores spreadsheet data including formulas, formatting, and multiple sheets.

## File Extensions

- `.xlsx` - Excel 2007+ files

## Implementation Details

### Reading

The XLSX implementation:
- Uses `openpyxl` library for reading
- Supports multiple sheets (by index or name)
- Extracts column headers from first row (if not specified)
- Iterates rows efficiently
- Converts each row to a dictionary

### Writing

Writing support:
- Uses `openpyxl` for writing
- Creates new Excel files
- Writes data row by row
- Supports multiple sheets

### Key Features

- **Multiple sheets**: Can read/write specific sheet by index or name
- **Header detection**: Automatically extracts headers from first row
- **Efficient iteration**: Uses row iterators for large files
- **Totals support**: Can count total rows
- **Write support**: Can create new Excel files

## Usage

```python
from iterable import open_iterable

# Basic reading (first sheet, headers from first row)
source = open_iterable('data.xlsx')
for row in source:
    print(row)
source.close()

# Read specific sheet by index
source = open_iterable('data.xlsx', iterableargs={
    'page': 1  # Second sheet (0-indexed)
})

# Read specific sheet by name
source = open_iterable('data.xlsx', iterableargs={
    'page': 'Sheet2'  # Sheet name
})

# List available sheets
from iterable.datatypes.xlsx import XLSXIterable

# Before opening - discover sheets
sheets = XLSXIterable('data.xlsx').list_tables('data.xlsx')
print(f"Available sheets: {sheets}")

# After opening - list all sheets
source = open_iterable('data.xlsx', iterableargs={'page': 0})
all_sheets = source.list_tables()  # Reuses open workbook
print(f"All sheets: {all_sheets}")

# Iterate over all sheets
for sheet_name in all_sheets:
    source = open_iterable('data.xlsx', iterableargs={'page': sheet_name})
    print(f"Processing sheet: {sheet_name}")
    for row in source:
        process(row)
    source.close()

# Writing
dest = open_iterable('output.xlsx', mode='w')
dest.write({'id': 1, 'name': 'John', 'age': 30})
dest.close()
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `page` | int or str | `0` | No | Sheet index (int, 0-indexed) or name (str) to read/write. Use `0` for first sheet, `1` for second sheet, or sheet name like `'Sheet2'`. |
| `keys` | list[str] | auto-detected | No | Column names. When reading, extracted from first row if not specified. When writing, required if first row doesn't contain headers. |
| `start_line` | int | `0` | No | Row number to start reading from (0-indexed). Useful for skipping header rows or starting at a specific row. |

## Error Handling

```python
from iterable import open_iterable

try:
    # Reading with error handling
    with open_iterable('data.xlsx', iterableargs={
        'page': 0  # or sheet name
    }) as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("XLSX file not found")
except ValueError as e:
    # May occur if sheet index/name is invalid
    print(f"Invalid sheet: {e}")
    # List available sheets first
    from iterable.datatypes.xlsx import XLSXIterable
    sheets = XLSXIterable('data.xlsx').list_tables('data.xlsx')
    print(f"Available sheets: {sheets}")
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install iterabledata[xlsx] or pip install openpyxl")
except Exception as e:
    print(f"Error reading XLSX: {e}")

try:
    # Writing with error handling
    with open_iterable('output.xlsx', mode='w', iterableargs={
        'page': 'Sheet1'  # Optional: specify sheet name
    }) as dest:
        dest.write({'id': 1, 'name': 'John', 'age': 30})
except KeyError as e:
    # May occur if keys parameter is required but not provided
    print(f"Missing required field: {e}")
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install iterabledata[xlsx] or pip install openpyxl")
except Exception as e:
    print(f"Error writing XLSX: {e}")
```

### Common Errors

- **ValueError**: Invalid sheet index or name - use `list_tables()` to see available sheets
- **ImportError**: Missing `openpyxl` package - install with `pip install openpyxl`
- **FileNotFoundError**: File path is incorrect or file doesn't exist
- **KeyError**: When writing, ensure all records have consistent keys or provide `keys` parameter

## Limitations

1. **openpyxl dependency**: Requires `openpyxl` package
2. **Flat data only**: Only supports tabular data
3. **File path required**: Requires filename, not stream
4. **Memory usage**: Large files may use significant memory
5. **Formatting**: Basic writing doesn't preserve Excel formatting
6. **Formulas**: Formulas are not evaluated, only values are read

## Compression Support

XLSX files are already ZIP archives internally, so additional compression may not provide much benefit. However, they can still be compressed:
- GZip (`.xlsx.gz`)
- BZip2 (`.xlsx.bz2`)
- LZMA (`.xlsx.xz`)
- LZ4 (`.xlsx.lz4`)
- ZIP (`.xlsx.zip`)
- Brotli (`.xlsx.br`)
- ZStandard (`.xlsx.zst`)

## Use Cases

- **Data analysis**: Processing Excel data
- **Reporting**: Generating Excel reports
- **Data migration**: Converting between formats
- **Business data**: Working with business spreadsheets

## Related Formats

- [XLS](xls.md) - Legacy Excel format (read-only)
- [ODS](ods.md) - OpenDocument Spreadsheet format
- [CSV](csv.md) - Simple text format
