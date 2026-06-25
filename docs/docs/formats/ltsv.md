# LTSV Format

## Description

LTSV (Labeled Tab-Separated Values) is a line-based data format where each line contains key-value pairs separated by tabs. Each field is in the format `key:value`, and fields are separated by tab characters. This format is commonly used for structured logging, especially in Japanese web services.

## File Extensions

- `.ltsv` - LTSV files

## Format Specification

Each line in an LTSV file represents a record:
- Fields are separated by tab characters (`\t`)
- Each field is a key-value pair in the format `key:value`
- Values can contain any characters (including tabs and newlines if properly escaped)
- Empty lines are skipped by default

### Example

```
time:2023-01-01T00:00:00Z	host:example.com	status:200	method:GET
time:2023-01-01T00:01:00Z	host:example.com	status:404	method:GET	path:/notfound
```

## Implementation Details

### Reading

The LTSV implementation:
- Parses each line by splitting on tab characters
- Extracts key-value pairs by splitting on the first colon
- Converts each line to a dictionary
- Skips empty lines by default

### Writing

The LTSV implementation:
- Formats dictionaries into LTSV lines
- Converts all values to strings
- Handles None values as empty strings
- Joins fields with tab characters

### Key Features

- **Simple format**: Easy to parse and generate
- **Structured data**: Each record is a dictionary
- **Flexible keys**: No predefined schema required
- **Totals support**: Can count total records
- **Read and write**: Full read/write support

## Usage

```python
from iterable.helpers.detect import open_iterable

# Basic reading
source = open_iterable('data.ltsv')
for row in source:
    print(row)
source.close()

# Writing
dest = open_iterable('output.ltsv', mode='w')
dest.write({
    'time': '2023-01-01T00:00:00Z',
    'host': 'example.com',
    'status': '200',
    'method': 'GET'
})
dest.close()
```

## Parameters

- `encoding` (str): File encoding (default: `utf-8`)

## Data Structure

Each record is returned as a dictionary:

```python
{
    'time': '2023-01-01T00:00:00Z',
    'host': 'example.com',
    'status': '200',
    'method': 'GET'
}
```

## Limitations

1. **Flat data only**: LTSV only supports flat key-value structures
2. **String values**: All values are treated as strings
3. **Tab separator**: Tab characters in values are not escaped (they would break parsing)
4. **No nested data**: Cannot represent nested structures

## Compression Support

LTSV files can be compressed with all supported codecs:
- GZip (`.ltsv.gz`)
- BZip2 (`.ltsv.bz2`)
- LZMA (`.ltsv.xz`)
- LZ4 (`.ltsv.lz4`)
- ZIP (`.ltsv.zip`)
- Brotli (`.ltsv.br`)
- ZStandard (`.ltsv.zst`)

## Use Cases

- **Structured logging**: Log files with labeled fields
- **Web server logs**: Custom log formats with key-value pairs
- **Application logs**: Structured application logging
- **Data exchange**: Simple key-value data exchange format

## Related Formats

- [CSV](csv.md) - Comma-separated values
- [TSV](csv.md) - Tab-separated values (without labels)
- [Apache Log](apachelog.md) - Apache web server logs
- [GELF](gelf.md) - Structured logging format
- Logfmt — similar key-value logging style (not a separate IterableData format)

## Example Files

### Reading LTSV

```python
from iterable.helpers.detect import open_iterable

source = open_iterable('access.ltsv')
for record in source:
    print(f"Time: {record.get('time')}, Status: {record.get('status')}")
source.close()
```

### Writing LTSV

```python
from iterable.helpers.detect import open_iterable

dest = open_iterable('output.ltsv', mode='w')
records = [
    {'time': '2023-01-01T00:00:00Z', 'host': 'example.com', 'status': '200'},
    {'time': '2023-01-01T00:01:00Z', 'host': 'example.com', 'status': '404'}
]
dest.write_bulk(records)
dest.close()
```

### Converting from CSV to LTSV

```python
from iterable.helpers.detect import open_iterable

source = open_iterable('data.csv')
dest = open_iterable('data.ltsv', mode='w')

for record in source:
    dest.write(record)

source.close()
dest.close()
```
