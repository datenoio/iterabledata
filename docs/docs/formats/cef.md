# CEF Format (Common Event Format)

## Description

CEF (Common Event Format) is a standard format for log and event data used in security information and event management (SIEM) systems. It's designed to be vendor-neutral and machine-readable, making it easy to integrate security events from different sources.

## File Extensions

- `.cef` - CEF format files

## Implementation Details

### Reading

The CEF implementation:
- Parses CEF-formatted log lines
- Extracts standard CEF fields (Version, Device Vendor, Device Product, etc.)
- Parses extension fields (key-value pairs)
- Converts each log line to a dictionary

### Writing

Writing is not currently supported for CEF format.

### Key Features

- **Standard format**: Industry-standard security event format
- **Structured parsing**: Converts log lines to structured data
- **Extension fields**: Handles key-value extension fields
- **Totals support**: Can count total log lines
- **SIEM integration**: Designed for SIEM systems

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('events.cef')
for row in source:
    print(row)
source.close()
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## CEF Format Structure

CEF format: `CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension`

Extension fields are key-value pairs separated by spaces, with keys and values separated by `=`.

## Limitations

1. **Read-only**: CEF format does not support writing
2. **Format-specific**: Must follow CEF format specification
3. **Extension parsing**: Complex extension fields may require manual handling
4. **Flat data only**: Only supports tabular log data

## Compression Support

CEF files can be compressed with all supported codecs:
- GZip (`.cef.gz`)
- BZip2 (`.cef.bz2`)
- LZMA (`.cef.xz`)
- LZ4 (`.cef.lz4`)
- ZIP (`.cef.zip`)
- Brotli (`.cef.br`)
- ZStandard (`.cef.zst`)

## Use Cases

- **SIEM systems**: Integrating with security information systems
- **Security logs**: Processing security event logs
- **Event correlation**: Correlating events from different sources
- **Compliance**: Meeting security logging requirements

## Related Formats

- [Apache Log](apachelog.md) - Web server log format
- [GELF](gelf.md) - Structured logging format
- [TXT](txt.md) - Plain text format
