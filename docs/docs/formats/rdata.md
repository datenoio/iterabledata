# RData Format

## Description

RData (`.rdata` or `.RData`) is R's native binary format for saving multiple R objects. It's commonly used in R statistical computing to save workspace data, including data frames, vectors, lists, and other R objects. This implementation supports reading RData files and converting them to Python dictionaries.

## File Extensions

- `.rdata` - RData files
- `.RData` - RData files (case-sensitive variant)
- `.rda` - RData files (alias)

## Implementation Details

### Reading

The RData implementation:
- Uses `pyreadr` library for reading
- Reads RData files which can contain multiple R objects
- Converts data frames to pandas DataFrames, then to dictionaries
- When multiple objects are present, adds `_r_object_name` metadata field to identify the source object
- Requires file path (not stream)

### Writing

Writing is not currently supported for RData format.

### Key Features

- **Multiple objects**: Can contain multiple R objects in a single file
- **Statistical format**: Designed for R statistical computing
- **Totals support**: Can count total rows across all objects
- **Type preservation**: Maintains data types from R
- **Object identification**: When multiple objects exist, adds metadata to identify source

## Usage

```python
from iterable import open_iterable

# List available R objects
from iterable.datatypes.rdata import RDataIterable

# Discover R objects before opening
objects = RDataIterable('data.rdata').list_tables('data.rdata')
print(f"Available R objects: {objects}")  # e.g., ['df1', 'df2', 'vector1']

# Basic reading
with open_iterable('data.rdata') as source:
    for row in source:
        print(row)
```

## Parameters

No specific parameters required.

## Limitations

1. **Read-only**: RData format does not support writing
2. **pyreadr dependency**: Requires `pyreadr` package
3. **File path required**: Requires filename, not stream
4. **Flat data only**: Only supports tabular data (data frames)
5. **Memory usage**: Entire file is loaded into memory
6. **Multiple objects**: When file contains multiple objects, they are flattened into a single stream

## Compression Support

RData files can be compressed with all supported codecs:
- GZip (`.rdata.gz`)
- BZip2 (`.rdata.bz2`)
- LZMA (`.rdata.xz`)
- LZ4 (`.rdata.lz4`)
- ZIP (`.rdata.zip`)
- Brotli (`.rdata.br`)
- ZStandard (`.rdata.zst`)

## Use Cases

- **Statistical analysis**: Working with R data files
- **Data migration**: Converting R data to other formats
- **Research data**: Processing research datasets in R format
- **Academic research**: Common in academic research and data science
- **R workspace files**: Reading saved R workspace files


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Read-only**: opening with `mode="w"` raises `WriteNotSupportedError` or `ValueError`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [RDS](rds.md) - R's single object format
- [SAS](sas.md) - SAS statistical format
- [Stata](stata.md) - Stata statistical format
- [SPSS](spss.md) - SPSS statistical format
- [CSV](csv.md) - Simple text format for conversion
