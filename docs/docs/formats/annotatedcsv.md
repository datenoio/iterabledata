# Annotated CSV Format (InfluxDB)

## Description

Annotated CSV is a format used by InfluxDB for exporting time series data. It extends standard CSV with metadata annotations that describe data types, groups, and other information. The format includes a header section with annotations followed by data rows.

## File Extensions

- `.annotatedcsv` - Annotated CSV files

## Implementation Details

### Reading

The Annotated CSV implementation:
- Parses InfluxDB Annotated CSV format
- Extracts metadata annotations from header
- Converts data types based on annotations
- Handles datetime, numeric, and boolean types
- Converts each row to a dictionary

### Writing

Writing is not currently supported for Annotated CSV format.

### Key Features

- **Type conversion**: Automatically converts values based on annotations
- **Metadata support**: Extracts and uses metadata annotations
- **InfluxDB format**: Designed for InfluxDB data export
- **Totals support**: Can count total rows
- **Time series**: Optimized for time series data

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('data.annotatedcsv')
for row in source:
    print(row)
source.close()
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)
- `delimiter` (str): Field delimiter (default: `,`)

## Limitations

1. **Read-only**: Annotated CSV format does not support writing
2. **InfluxDB-specific**: Designed specifically for InfluxDB
3. **Format complexity**: Requires understanding of InfluxDB annotations
4. **Type conversion**: Some complex types may not convert perfectly

## Compression Support

Annotated CSV files can be compressed with all supported codecs:
- GZip (`.annotatedcsv.gz`)
- BZip2 (`.annotatedcsv.bz2`)
- LZMA (`.annotatedcsv.xz`)
- LZ4 (`.annotatedcsv.lz4`)
- ZIP (`.annotatedcsv.zip`)
- Brotli (`.annotatedcsv.br`)
- ZStandard (`.annotatedcsv.zst`)

## Use Cases

- **InfluxDB export**: Exporting data from InfluxDB
- **Time series data**: Working with time series data
- **Data migration**: Migrating InfluxDB data
- **Data analysis**: Analyzing time series data

## Related Formats

- [CSV](csv.md) - Standard CSV format
- [ILP](ilp.md) - InfluxDB Line Protocol format
