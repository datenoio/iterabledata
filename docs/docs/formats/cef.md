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

Writing support:
- Reconstructs CEF lines from standard fields plus extension key/values
- Escapes `|`, `=`, and newlines in extension values

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
with open_iterable('events.cef') as source:
    for row in source:
        print(row)

# Writing
with open_iterable('output.cef', mode='w') as dest:
    dest.write({
        'device_vendor': 'Example',
        'device_product': 'App',
        'name': 'Login',
        'severity': '5',
        'src': '10.0.0.1',
    })
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## CEF Format Structure

CEF format: `CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension`

Extension fields are key-value pairs separated by spaces, with keys and values separated by `=`.

## Limitations

1. **Format-specific**: Must follow CEF format specification
2. **Extension parsing**: Complex extension fields may require manual handling
3. **Flat data only**: Only supports tabular log data

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


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [Apache Log](apachelog.md) - Web server log format
- [GELF](gelf.md) - Structured logging format
- [TXT](txt.md) - Plain text format
