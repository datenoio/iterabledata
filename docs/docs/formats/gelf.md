# GELF Format (Graylog Extended Log Format)

## Description

GELF (Graylog Extended Log Format) is a JSON-based log format used by Graylog and other log management systems. It's similar to JSONL but with specific fields required by the GELF specification. GELF messages are JSON objects sent one per line.

## File Extensions

- `.gelf` - GELF format files

## Implementation Details

### Reading

The GELF implementation:
- Reads JSONL-style format (one JSON object per line)
- Parses each line as a JSON object
- Validates GELF-specific fields (version, timestamp, short_message)
- Converts each log entry to a dictionary

### Writing

Writing support:
- Writes GELF-formatted JSON objects
- Validates required GELF fields
- Writes one JSON object per line

### Key Features

- **JSON-based**: Uses JSON format
- **Structured logging**: Designed for structured log data
- **GELF validation**: Validates GELF-specific fields
- **Totals support**: Can count total log lines
- **Nested data**: Supports complex nested structures

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('logs.gelf')
for row in source:
    print(row)
source.close()

# Writing
dest = open_iterable('output.gelf', mode='w')
dest.write({
    'version': '1.1',
    'host': 'server1',
    'short_message': 'Test message',
    'timestamp': 1234567890.123,
    'level': 6
})
dest.close()
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## GELF Required Fields

- `version` (string): GELF version (e.g., "1.1")
- `timestamp` (number): Unix timestamp
- `short_message` or `message` (string): Log message

## Limitations

1. **GELF validation**: Requires GELF-specific fields
2. **Line-based**: Each record must fit on a single line
3. **JSON parsing**: Invalid JSON will cause errors
4. **Field requirements**: Must include required GELF fields

## Compression Support

GELF files can be compressed with all supported codecs:
- GZip (`.gelf.gz`)
- BZip2 (`.gelf.bz2`)
- LZMA (`.gelf.xz`)
- LZ4 (`.gelf.lz4`)
- ZIP (`.gelf.zip`)
- Brotli (`.gelf.br`)
- ZStandard (`.gelf.zst`)

## Use Cases

- **Graylog**: Integrating with Graylog log management
- **Structured logging**: Structured log data collection
- **Log aggregation**: Aggregating logs from multiple sources
- **Monitoring**: Application and system monitoring

## Related Formats

- [JSONL](jsonl.md) - Similar line-delimited JSON format
- [Apache Log](apachelog.md) - Web server log format
- [CEF](cef.md) - Security event format
