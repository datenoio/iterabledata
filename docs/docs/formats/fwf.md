# Fixed Width Format (FWF)

## Description

Fixed Width Format (FWF) is a text format where each field has a fixed width in characters. This format is common in legacy systems and mainframe data exports. Fields are positioned at specific column positions, and values are padded or truncated to fit the specified width.

## File Extensions

- `.fwf` - Fixed width format files
- `.fixed` - Fixed width format files (alias)

## Implementation Details

### Reading

The FWF implementation:
- Requires `widths` and `names` parameters
- Reads line by line
- Extracts fields based on column positions
- Strips whitespace from field values

### Writing

Writing support:
- Requires `widths` and `names` parameters
- Pads or truncates values to fit field widths
- Writes fixed-width lines

### Key Features

- **Column-based**: Fields defined by column positions
- **Totals support**: Can count total rows
- **Encoding support**: Handles various text encodings
- **Simple format**: Easy to parse and generate

## Usage

```python
from iterable import open_iterable

# Reading fixed-width file
source = open_iterable('data.fwf', iterableargs={
    'widths': [10, 20, 15],  # Width of each field
    'names': ['id', 'name', 'date'],  # Field names
    'encoding': 'utf-8'
})
for row in source:
    print(row)
source.close()

# Writing fixed-width file
dest = open_iterable('output.fwf', mode='w', iterableargs={
    'widths': [10, 20, 15],
    'names': ['id', 'name', 'date']
})
dest.write({'id': '1', 'name': 'John', 'date': '2024-01-01'})
dest.close()
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `widths` | list[int] | None | **Yes** | Width of each field in characters. Must match the number of fields in the file. Example: `[10, 20, 15]` for three fields. |
| `names` | list[str] | None | **Yes** | Names of each field. Must have same length as `widths`. Example: `['id', 'name', 'date']`. |
| `encoding` | str | `utf8` | No | File encoding for reading/writing fixed-width files. Common values: `utf-8`, `latin-1`, `cp1252`. |

## Error Handling

```python
from iterable import open_iterable

try:
    # Reading with error handling
    with open_iterable('data.fwf', iterableargs={
        'widths': [10, 20, 15],  # Required
        'names': ['id', 'name', 'date'],  # Required
        'encoding': 'utf-8'
    }) as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("FWF file not found")
except ValueError as e:
    # May occur if widths/names are missing or mismatched
    print(f"Invalid parameters: {e}")
    print("Ensure 'widths' and 'names' are provided and have same length")
except KeyError as e:
    # May occur when writing if record missing required field
    print(f"Missing required field: {e}")
except UnicodeDecodeError:
    print("Encoding error - try specifying encoding explicitly")
    with open_iterable('data.fwf', iterableargs={
        'widths': [10, 20, 15],
        'names': ['id', 'name', 'date'],
        'encoding': 'latin-1'
    }) as source:
        for row in source:
            process(row)
except Exception as e:
    print(f"Error reading FWF: {e}")

try:
    # Writing with error handling
    with open_iterable('output.fwf', mode='w', iterableargs={
        'widths': [10, 20, 15],
        'names': ['id', 'name', 'date']
    }) as dest:
        dest.write({'id': '1', 'name': 'John', 'date': '2024-01-01'})
except ValueError as e:
    print(f"Invalid parameters: {e}")
    print("Ensure 'widths' and 'names' are provided and have same length")
except KeyError as e:
    print(f"Missing required field in record: {e}")
except Exception as e:
    print(f"Error writing FWF: {e}")
```

### Common Errors

- **ValueError**: Missing or mismatched `widths` and `names` parameters - both are required and must have same length
- **KeyError**: Missing required field when writing - ensure all records contain all field names
- **UnicodeDecodeError**: Encoding issue - specify correct encoding
- **FileNotFoundError**: File path is incorrect or file doesn't exist

## Limitations

1. **Parameters required**: Must specify `widths` and `names` for both reading and writing
2. **No nested data**: Only supports flat, tabular data
3. **Fixed structure**: Field positions cannot vary
4. **Truncation**: Values longer than field width are truncated
5. **Padding**: Values shorter than field width are padded with spaces
6. **No type information**: All values are strings

## Compression Support

FWF files can be compressed with all supported codecs:
- GZip (`.fwf.gz`)
- BZip2 (`.fwf.bz2`)
- LZMA (`.fwf.xz`)
- LZ4 (`.fwf.lz4`)
- ZIP (`.fwf.zip`)
- Brotli (`.fwf.br`)
- ZStandard (`.fwf.zst`)

## Use Cases

- **Legacy systems**: Working with mainframe data exports
- **Banking**: Financial data formats
- **Government data**: Official data formats
- **Data migration**: Converting from legacy systems

## Related Formats

- [CSV](csv.md) - Delimiter-separated format
- [PSV](psv.md) - Pipe-separated format
