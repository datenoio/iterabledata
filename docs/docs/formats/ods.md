# ODS Format (OpenDocument Spreadsheet)

## Description

ODS (OpenDocument Spreadsheet) is an open standard spreadsheet format used by LibreOffice, OpenOffice, and other office suites. It's an XML-based format stored in a ZIP archive, similar to XLSX but using open standards.

## File Extensions

- `.ods` - OpenDocument Spreadsheet files

## Implementation Details

### Reading

The ODS implementation:
- Uses `odfpy` library (preferred) or `pyexcel-ods3` library
- Supports multiple sheets (pages)
- Extracts column headers from first row (if not specified)
- Converts each row to a dictionary
- Requires file path (not stream)

### Writing

Writing support:
- Creates ODS files
- Writes data to sheets
- Supports multiple sheets

### Key Features

- **Multiple sheets**: Can read/write from specific sheet
- **Header detection**: Automatically extracts headers from first row
- **Open standard**: Open format, not proprietary
- **Totals support**: Can count total rows

## Usage

```python
from iterable import open_iterable

# Basic reading (first sheet, headers from first row)
source = open_iterable('data.ods')
for row in source:
    print(row)
source.close()

# Read specific sheet
source = open_iterable('data.ods', iterableargs={
    'page': 1  # Second sheet (0-indexed)
})

# List available sheets
from iterable.datatypes.ods import ODSIterable

# Discover sheets before opening
sheets = ODSIterable('data.ods').list_tables('data.ods')
print(f"Available sheets: {sheets}")

# List sheets after opening (reuses document)
source = open_iterable('data.ods', iterableargs={'page': 0})
all_sheets = source.list_tables()  # Reuses open document
print(f"All sheets: {all_sheets}")
source.close()

# Writing
dest = open_iterable('output.ods', mode='w')
dest.write({'id': 1, 'name': 'John', 'age': 30})
dest.close()
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `page` | int | `0` | No | Sheet index to read/write (0-indexed). Use `0` for first sheet, `1` for second sheet, etc. |
| `keys` | list[str] | auto-detected | No | Column names. When reading, extracted from first row if not specified. When writing, required if first row doesn't contain headers. |
| `start_line` | int | `0` | No | Row number to start reading from (0-indexed). Useful for skipping header rows or starting at a specific row. |

## Error Handling

```python
from iterable import open_iterable

try:
    # Reading with error handling
    with open_iterable('data.ods', iterableargs={
        'page': 0  # Sheet index
    }) as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("ODS file not found")
except ValueError as e:
    # May occur if sheet index is invalid
    print(f"Invalid sheet index: {e}")
    # List available sheets first
    from iterable.datatypes.ods import ODSIterable
    sheets = ODSIterable('data.ods').list_tables('data.ods')
    print(f"Available sheets: {sheets}")
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install iterabledata[ods] or pip install odfpy")
except Exception as e:
    print(f"Error reading ODS: {e}")

try:
    # Writing with error handling
    with open_iterable('output.ods', mode='w') as dest:
        dest.write({'id': 1, 'name': 'John', 'age': 30})
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install iterabledata[ods] or pip install odfpy")
except Exception as e:
    print(f"Error writing ODS: {e}")
```

### Common Errors

- **ValueError**: Invalid sheet index - use `list_tables()` to see available sheets
- **ImportError**: Missing `odfpy` package - install with `pip install odfpy`
- **FileNotFoundError**: File path is incorrect or file doesn't exist

## Limitations

1. **Dependency**: Requires `odfpy` or `pyexcel-ods3` package
2. **File path required**: Requires filename, not stream
3. **Flat data only**: Only supports tabular data
4. **Memory usage**: Large files may use significant memory
5. **Formatting**: Basic writing doesn't preserve spreadsheet formatting

## Compression Support

ODS files are already ZIP archives internally, so additional compression may not provide much benefit. However, they can still be compressed:
- GZip (`.ods.gz`)
- BZip2 (`.ods.bz2`)
- LZMA (`.ods.xz`)
- LZ4 (`.ods.lz4`)
- ZIP (`.ods.zip`)
- Brotli (`.ods.br`)
- ZStandard (`.ods.zst`)

## Use Cases

- **OpenOffice/LibreOffice**: Working with open office suite files
- **Data migration**: Converting from proprietary formats
- **Open standards**: When you need open, non-proprietary format
- **Cross-platform**: Compatible across different office suites

## Related Formats

- [XLSX](xlsx.md) - Microsoft Excel format
- [XLS](xls.md) - Legacy Excel format
- [CSV](csv.md) - Simple text format
