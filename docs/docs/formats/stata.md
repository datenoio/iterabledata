# Stata Format

## Description

Stata is a statistical software package, and `.dta` files are Stata's native data file format. This implementation supports reading Stata files and converting them to Python dictionaries.

## File Extensions

- `.dta` - Stata data files
- `.stata` - Stata files (alias)

## Implementation Details

### Reading

The Stata implementation:
- Uses `pyreadstat` library for reading
- Reads Stata files and converts to pandas DataFrame, then to dictionaries
- Supports metadata extraction (variable labels, value labels)
- Requires file path (not stream)

### Writing

Writing is not currently supported for Stata format.

### Key Features

- **Statistical format**: Designed for statistical analysis
- **Metadata support**: Can extract variable labels and value labels
- **Totals support**: Can count total rows
- **Type preservation**: Maintains data types from Stata

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.dta') as source:
    for row in source:
        print(row)
```

## Parameters

No specific parameters required.

## Limitations

1. **Read-only**: Stata format does not support writing
2. **pyreadstat dependency**: Requires `pyreadstat` package
3. **File path required**: Requires filename, not stream
4. **Flat data only**: Only supports tabular data
5. **Memory usage**: Entire file is loaded into memory

## Compression Support

Stata files can be compressed with all supported codecs:
- GZip (`.dta.gz`)
- BZip2 (`.dta.bz2`)
- LZMA (`.dta.xz`)
- LZ4 (`.dta.lz4`)
- ZIP (`.dta.zip`)
- Brotli (`.dta.br`)
- ZStandard (`.dta.zst`)

## Use Cases

- **Statistical analysis**: Working with Stata data files
- **Data migration**: Converting Stata data to other formats
- **Research data**: Processing research datasets in Stata format
- **Academic research**: Common in academic research


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Read-only**: opening with `mode="w"` raises `WriteNotSupportedError` or `ValueError`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [SAS](sas.md) - SAS statistical format
- [SPSS](spss.md) - SPSS statistical format
- [CSV](csv.md) - Simple text format for conversion
