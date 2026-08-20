# SAS Format

## Description

SAS (Statistical Analysis System) files are binary data files used by SAS software for statistical analysis. The `.sas7bdat` format is the native SAS data file format. This implementation supports reading SAS files and converting them to Python dictionaries.

## File Extensions

- `.sas` - SAS files
- `.sas7bdat` - SAS 7 binary data files

## Implementation Details

### Reading

The SAS implementation:
- Uses `pyreadstat` (`pip install iterabledata[stats]`)
- Reads SAS files and converts to pandas DataFrame, then to dictionaries
- Supports metadata extraction
- Requires file path (not stream)

### Writing

Writing is not currently supported for SAS format.

### Key Features

- **Statistical format**: Designed for statistical analysis
- **Metadata support**: Can extract variable labels and formats
- **Totals support**: Can count total rows
- **Type preservation**: Maintains data types from SAS

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.sas7bdat') as source:
    for row in source:
        print(row)
```

## Parameters

No specific parameters required.

## Limitations

1. **Read-only**: SAS format does not support writing
2. **Dependency**: Requires `pip install iterabledata[stats]` (`pyreadstat`)
3. **File path required**: Requires filename, not stream
4. **Flat data only**: Only supports tabular data
5. **Memory usage**: Entire file is loaded into memory

## Compression Support

SAS files can be compressed with all supported codecs:
- GZip (`.sas7bdat.gz`)
- BZip2 (`.sas7bdat.bz2`)
- LZMA (`.sas7bdat.xz`)
- LZ4 (`.sas7bdat.lz4`)
- ZIP (`.sas7bdat.zip`)
- Brotli (`.sas7bdat.br`)
- ZStandard (`.sas7bdat.zst`)

## Use Cases

- **Statistical analysis**: Working with SAS data files
- **Data migration**: Converting SAS data to other formats
- **Research data**: Processing research datasets in SAS format
- **Government data**: Some government datasets use SAS format


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Read-only**: opening with `mode="w"` raises `WriteNotSupportedError` or `ValueError`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [Stata](stata.md) - Another statistical format
- [SPSS](spss.md) - SPSS statistical format
- [CSV](csv.md) - Simple text format for conversion
