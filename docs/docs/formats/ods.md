# ODS Format (OpenDocument Spreadsheet)

## Description

ODS (OpenDocument Spreadsheet) is an open standard spreadsheet format used by LibreOffice, OpenOffice, and other office suites. It's an XML-based format stored in a ZIP archive, similar to XLSX but using open standards.

## File Extensions

- `.ods` - OpenDocument Spreadsheet files

## Implementation Details

### Reading

The ODS implementation:
- Uses `odfpy` (preferred) or `pyexcel-ods3`
- Supports multiple sheets (pages)
- Extracts column headers from the first row when not specified
- Converts each row to a dictionary
- Requires a file path (not a stream)

### Writing

Writing is **not supported**. `write()` / `write_bulk()` raise `WriteNotSupportedError`. Convert to [CSV](csv.md) or [Parquet](parquet.md) for output.

### Key Features

- **Multiple sheets**: Read a specific sheet by index
- **Header detection**: Automatically extracts headers from the first row
- **Open standard**: Not a proprietary Excel format
- **Totals support**: Can count total rows
- **Read-only**: No ODS writer in this release

## Usage

```python
from iterable import open_iterable
from iterable.datatypes.ods import ODSIterable

with open_iterable("data.ods") as source:
    for row in source:
        print(row)

with open_iterable("data.ods", iterableargs={"page": 1}) as source:
    for row in source:
        print(row)

sheets = ODSIterable("data.ods").list_tables("data.ods")
print("Available sheets:", sheets)
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `page` | int | `0` | No | Sheet index to read (0-indexed) |
| `keys` | list[str] | auto-detected | No | Column names. Extracted from the first row if omitted. |
| `start_line` | int | `0` | No | Row number to start reading from (0-indexed) |

## Error Handling

```python
from iterable import open_iterable
from iterable.datatypes.ods import ODSIterable

try:
    with open_iterable("data.ods", iterableargs={"page": 0}) as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("ODS file not found")
except ValueError as e:
    print(f"Invalid sheet index: {e}")
    print("Available sheets:", ODSIterable("data.ods").list_tables("data.ods"))
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install iterabledata[ods]")
```

### Common Errors

- **ValueError**: Invalid sheet index — use `list_tables()` first
- **ImportError**: Missing `odfpy` — `pip install iterabledata[ods]`
- **WriteNotSupportedError**: Writing ODS is not implemented

## Limitations

1. **Dependency**: Requires `odfpy` or `pyexcel-ods3`
2. **File path required**: Filename, not a stream
3. **Flat data only**
4. **Read-only**

## Related Formats

- [XLSX](xlsx.md) - Microsoft Excel (read-only)
- [XLS](xls.md) - Legacy Excel (read-only)
- [CSV](csv.md) - Writable tabular text
