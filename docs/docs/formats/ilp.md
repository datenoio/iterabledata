# ILP Format (InfluxDB Line Protocol)

## Description

ILP (InfluxDB Line Protocol) is a text-based format used by InfluxDB for writing time series data. Each line represents a single data point with measurement name, tags, fields, and optional timestamp. It's designed for high-throughput data ingestion.

## File Extensions

- `.ilp` - InfluxDB Line Protocol files

## Implementation Details

### Reading

The ILP implementation:
- Parses InfluxDB Line Protocol format
- Extracts measurement, tags, fields, and timestamp
- Handles escaped characters and special values
- Converts each line to a dictionary
- Supports streaming for large files

### Writing

Writing support:
- Writes ILP-formatted lines
- Formats measurement, tags, fields, and timestamp
- Handles escaping of special characters

### Key Features

- **Line-based**: One data point per line
- **Time series**: Designed for time series data
- **High throughput**: Optimized for fast ingestion
- **Totals support**: Can count total lines
- **Streaming**: Processes files line by line

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.ilp') as source:
    for row in source:
        print(row)  # Contains: measurement, tags, fields, time

# Writing
with open_iterable('output.ilp', mode='w') as dest:
    dest.write({
        'measurement': 'temperature',
        'tags': {'location': 'room1', 'sensor': 'A1'},
        'fields': {'value': 23.5},
        'time': 1234567890000000000  # Nanosecond timestamp
    })
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## ILP Format Structure

Format: `measurement[,tag_key=tag_value] field_key=field_value[,field_key=field_value] [timestamp]`

- **measurement**: Measurement name
- **tags**: Optional key-value pairs (comma-separated)
- **fields**: Required key-value pairs (comma-separated)
- **timestamp**: Optional nanosecond timestamp

## Limitations

1. **Line-based format**: Each record must fit on a single line
2. **Format-specific**: Must follow ILP format specification
3. **Escaping complexity**: Special characters must be properly escaped
4. **Time series focus**: Designed specifically for time series data

## Compression Support

ILP files can be compressed with all supported codecs:
- GZip (`.ilp.gz`)
- BZip2 (`.ilp.bz2`)
- LZMA (`.ilp.xz`)
- LZ4 (`.ilp.lz4`)
- ZIP (`.ilp.zip`)
- Brotli (`.ilp.br`)
- ZStandard (`.ilp.zst`)

## Use Cases

- **InfluxDB ingestion**: Writing data to InfluxDB
- **Time series data**: Processing time series data
- **IoT data**: Collecting IoT sensor data
- **Monitoring**: System and application monitoring

## Related Formats

- [Annotated CSV](annotatedcsv.md) - InfluxDB export format
- [CSV](csv.md) - Standard CSV format
