# PC-Axis (PX) Format

## Description

PC-Axis (PX) is a statistical data format developed by Statistics Sweden and used by many statistical offices worldwide. It's a text-based format designed for exchanging multi-dimensional statistical data with metadata. The format supports hierarchical data structures with dimensions (stub and heading variables) that are flattened into tabular records.

## File Extensions

- `.px` - PC-Axis statistical data files

## Implementation Details

### Reading

The PC-Axis implementation:
- Parses metadata section (TITLE, STUB, HEADING, VALUES, CODES, etc.)
- Parses data section (numeric values)
- Flattens multi-dimensional data into tabular records
- Converts numeric values to appropriate types (int/float)
- Preserves metadata as record fields (prefixed with `_`)
- Supports various character encodings

### Writing

Writing is not currently supported for PC-Axis format.

### Key Features

- **Multi-dimensional data**: Handles statistical data with multiple dimensions
- **Metadata preservation**: Includes metadata fields in output records
- **Automatic flattening**: Converts multi-dimensional arrays to flat records
- **Totals support**: Can count total records
- **Encoding support**: Handles various character encodings
- **Statistical format**: Designed for official statistics

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('data.px')
for row in source:
    print(row)
    # Each row contains dimension variables and a VALUE field
source.close()

# With specific encoding
source = open_iterable('data.px', iterableargs={
    'encoding': 'iso-8859-1'  # Common for European statistical data
})

# Check total records
source = open_iterable('data.px')
total = source.totals()
print(f"Total records: {total}")
source.close()
```

## Record Structure

Each record contains:
- **Dimension variables**: Fields from STUB and HEADING declarations (e.g., `Age`, `Gender`, `Year`)
- **VALUE**: The numeric data value for that combination of dimensions
- **Metadata fields**: Additional metadata prefixed with `_` (e.g., `_TITLE`, `_CONTENTS`)

Example record:
```python
{
    'Age': '0-4',
    'Gender': 'Male',
    'Year': '2020',
    'VALUE': 100,
    '_TITLE': 'Population Statistics',
    '_CONTENTS': 'Number of persons'
}
```

## Parameters

- `encoding` (str): Character encoding (default: `utf-8`)

## Limitations

1. **Read-only**: PC-Axis format does not support writing
2. **Flat data only**: Only supports tabular/flat data structures
3. **Multi-dimensional flattening**: Complex multi-dimensional data is flattened into records
4. **File format**: Requires proper PC-Axis file structure
5. **Encoding**: May require specific encoding for non-ASCII data

## Compression Support

PC-Axis files can be compressed with all supported codecs:
- GZip (`.px.gz`)
- BZip2 (`.px.bz2`)
- LZMA (`.px.xz`)
- LZ4 (`.px.lz4`)
- ZIP (`.px.zip`)
- Brotli (`.px.br`)
- ZStandard (`.px.zst`)
- Snappy (`.px.snappy`)
- LZO (`.px.lzo`)

## Use Cases

- **Official statistics**: Reading data from statistical offices
- **Government data**: Many government agencies use PC-Axis format
- **Data analysis**: Converting statistical data for analysis
- **Data migration**: Converting from PC-Axis to other formats
- **Research**: Working with official statistical datasets

## Related Formats

- [CSV](csv.md) - Simple text format
- [SAS](sas.md) - Statistical analysis format
- [Stata](stata.md) - Statistical software format
- [SPSS](spss.md) - Statistical package format

