# SPSS Format

## Description

SPSS (Statistical Package for the Social Sciences) files are binary data files used by SPSS software for statistical analysis. The `.sav` format is SPSS's native data file format. This implementation supports reading SPSS files and converting them to Python dictionaries.

## File Extensions

- `.sav` - SPSS data files
- `.spss` - SPSS files (alias)

## Implementation Details

### Reading

The SPSS implementation:
- Uses `pyreadstat` library for reading
- Reads SPSS files and converts to pandas DataFrame, then to dictionaries
- Supports metadata extraction (variable labels, value labels)
- Requires file path (not stream)

### Writing

Writing is not currently supported for SPSS format.

### Key Features

- **Statistical format**: Designed for statistical analysis
- **Metadata support**: Can extract variable labels and value labels
- **Totals support**: Can count total rows
- **Type preservation**: Maintains data types from SPSS

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.sav') as source:
    for row in source:
        print(row)
```

## Parameters

No specific parameters required.

## Limitations

1. **Read-only**: SPSS format does not support writing
2. **pyreadstat dependency**: Requires `pyreadstat` package
3. **File path required**: Requires filename, not stream
4. **Flat data only**: Only supports tabular data
5. **Memory usage**: Entire file is loaded into memory

## Compression Support

SPSS files can be compressed with all supported codecs:
- GZip (`.sav.gz`)
- BZip2 (`.sav.bz2`)
- LZMA (`.sav.xz`)
- LZ4 (`.sav.lz4`)
- ZIP (`.sav.zip`)
- Brotli (`.sav.br`)
- ZStandard (`.sav.zst`)

## Use Cases

- **Statistical analysis**: Working with SPSS data files
- **Data migration**: Converting SPSS data to other formats
- **Research data**: Processing research datasets in SPSS format
- **Social sciences**: Common in social science research


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Read-only**: opening with `mode="w"` raises `WriteNotSupportedError` or `ValueError`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [SAS](sas.md) - SAS statistical format
- [Stata](stata.md) - Stata statistical format
- [CSV](csv.md) - Simple text format for conversion
