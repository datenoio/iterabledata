# TXT Format (Plain Text)

## Description

TXT format handles plain text files line by line. It's a flexible format that can be used with custom parsers to convert lines into structured data. Without a parser, it returns lines as strings.

## File Extensions

- `.txt` - Text files
- `.text` - Text files (alias)

## Implementation Details

### Reading

The TXT implementation:
- Reads file line by line
- Can use custom parser function to convert lines to dictionaries
- Without parser, returns lines as strings
- Supports streaming for large files

### Writing

Writing support:
- Writes lines to file
- If parser provided, expects dictionaries (converts to strings)
- Without parser, writes strings directly

### Key Features

- **Flexible**: Can work with or without parser
- **Custom parsing**: Supports custom line parsing functions
- **Streaming**: Processes files line by line
- **Totals support**: Can count total lines

## Usage

```python
from iterable import open_iterable

# Basic reading (returns strings)
with open_iterable('data.txt') as source:
    for line in source:
        print(line)  # line is a string

# With custom parser
def parse_log_line(line):
    parts = line.split(' ')
    return {
        'timestamp': parts[0],
        'level': parts[1],
        'message': ' '.join(parts[2:])
    }

with open_iterable('log.txt', iterableargs={
    'parser': parse_log_line
}) as source:
    for record in source:
        print(record)  # record is a dict
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)
- `parser` (callable): Optional function to parse each line into a dictionary

## Limitations

1. **Parser requirement**: For structured data, requires custom parser
2. **Line-based**: Each record must fit on a single line
3. **No standard format**: No built-in structure parsing
4. **Write limitations**: Writing dictionaries requires parser or manual conversion

## Compression Support

TXT files can be compressed with all supported codecs:
- GZip (`.txt.gz`)
- BZip2 (`.txt.bz2`)
- LZMA (`.txt.xz`)
- LZ4 (`.txt.lz4`)
- ZIP (`.txt.zip`)
- Brotli (`.txt.br`)
- ZStandard (`.txt.zst`)

## Use Cases

- **Log files**: Processing log files with custom parsers
- **Custom formats**: Working with custom text-based formats
- **Line-by-line processing**: When you need line-by-line access
- **Data transformation**: Converting text to structured data


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [Apache Log](apachelog.md) - Structured log format
- [GELF](gelf.md) - Structured logging format
- [CEF](cef.md) - Common Event Format
