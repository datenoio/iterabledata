# RDS Format

## Description

RDS (`.rds`) is R's native binary format for saving a single R object. It's commonly used in R statistical computing to save individual data frames, vectors, lists, or other R objects. Unlike RData which can save multiple objects, RDS saves exactly one object. This implementation supports reading RDS files and converting them to Python dictionaries.

## File Extensions

- `.rds` - RDS files

## Implementation Details

### Reading

The RDS implementation:
- Uses `pyreadr` library for reading
- Reads RDS files which contain a single R object
- Converts data frames to pandas DataFrames, then to dictionaries
- Requires file path (not stream)

### Writing

Writing is not currently supported for RDS format.

### Key Features

- **Single object**: Contains exactly one R object
- **Statistical format**: Designed for R statistical computing
- **Totals support**: Can count total rows
- **Type preservation**: Maintains data types from R
- **Efficient**: More efficient than RData for single objects

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('data.rds')
for row in source:
    print(row)
source.close()
```

## Parameters

No specific parameters required.

## Limitations

1. **Read-only**: RDS format does not support writing
2. **pyreadr dependency**: Requires `pyreadr` package
3. **File path required**: Requires filename, not stream
4. **Flat data only**: Only supports tabular data (data frames)
5. **Memory usage**: Entire file is loaded into memory
6. **Single object**: File must contain a single object (typically a data frame)

## Compression Support

RDS files can be compressed with all supported codecs:
- GZip (`.rds.gz`)
- BZip2 (`.rds.bz2`)
- LZMA (`.rds.xz`)
- LZ4 (`.rds.lz4`)
- ZIP (`.rds.zip`)
- Brotli (`.rds.br`)
- ZStandard (`.rds.zst`)

## Use Cases

- **Statistical analysis**: Working with R data files
- **Data migration**: Converting R data to other formats
- **Research data**: Processing research datasets in R format
- **Academic research**: Common in academic research and data science
- **Single object storage**: Saving and loading individual R objects

## Related Formats

- [RData](rdata.md) - R's multiple object format
- [SAS](sas.md) - SAS statistical format
- [Stata](stata.md) - Stata statistical format
- [SPSS](spss.md) - SPSS statistical format
- [CSV](csv.md) - Simple text format for conversion
