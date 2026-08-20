# Apache Log Format

## Description

Apache Log format is used by Apache HTTP Server for logging HTTP requests. The implementation supports Common Log Format, Combined Log Format, and Virtual Host Common Log Format. Each log line is parsed into structured fields.

## File Extensions

- `.log` - Log files
- `.access.log` - Apache access log files

## Implementation Details

### Reading

The Apache Log implementation:
- Parses log lines using regular expressions
- Supports multiple log formats (common, combined, vhost_common)
- Extracts fields like IP address, timestamp, request method, status code, etc.
- Converts each log line to a dictionary

### Writing

Writing support:
- Reconstructs Common, Combined, or vhost_common lines from parsed fields
- Uses the same `log_format` argument as reading

### Key Features

- **Multiple formats**: Supports common, combined, and vhost_common formats
- **Structured parsing**: Converts log lines to structured data
- **Totals support**: Can count total log lines
- **Field extraction**: Extracts all standard Apache log fields

## Usage

```python
from iterable import open_iterable

# Basic reading (default: common format)
with open_iterable('access.log') as source:
    for row in source:
        print(row)

# Combined format
source = open_iterable('access.log', iterableargs={
    'log_format': 'combined'  # or 'common', 'vhost_common'
})

# Writing
with open_iterable('output.log', mode='w', iterableargs={'log_format': 'common'}) as dest:
    dest.write({
        'remote_host': '127.0.0.1',
        'method': 'GET',
        'request': '/',
        'protocol': 'HTTP/1.1',
        'status': '200',
        'size': '123',
    })
```

## Parameters

- `log_format` (str): Log format type (default: `common`)
  - Options: `common`, `combined`, `vhost_common`

## Log Format Fields

### Common Format
- `remote_host`, `remote_logname`, `remote_user`, `time`, `method`, `request`, `protocol`, `status`, `size`

### Combined Format
- All common fields plus: `referer`, `user_agent`

### Virtual Host Common Format
- Similar to common but without remote_logname

## Limitations

1. **Format-specific**: Must match one of the supported formats
2. **Regex parsing**: Uses regex which may not handle all edge cases
3. **Flat data only**: Only supports tabular log data

## Compression Support

Apache log files can be compressed with all supported codecs:
- GZip (`.log.gz`)
- BZip2 (`.log.bz2`)
- LZMA (`.log.xz`)
- LZ4 (`.log.lz4`)
- ZIP (`.log.zip`)
- Brotli (`.log.br`)
- ZStandard (`.log.zst`)

## Use Cases

- **Web server logs**: Processing Apache web server logs
- **Log analysis**: Analyzing web server access patterns
- **Security analysis**: Detecting suspicious access patterns
- **Traffic analysis**: Understanding website traffic

## Related Formats

- [GELF](gelf.md) - Structured logging format
- [CEF](cef.md) - Common Event Format
- [TXT](txt.md) - Plain text format
