# EDN Format (Extensible Data Notation)

## Description

EDN (Extensible Data Notation) is a data format used in Clojure. It's similar to JSON but supports more data types and is extensible. EDN is a subset of Clojure's literal syntax and is used for data interchange in Clojure applications.

## File Extensions

- `.edn` - EDN format files

## Implementation Details

### Reading

The EDN implementation:
- Uses `edn_format` or `pyedn` library for parsing
- Parses EDN data structures
- Supports multiple EDN values (line-delimited)
- Converts EDN data to Python objects

### Writing

Writing support:
- Encodes Python objects to EDN format
- Writes EDN data
- Supports nested structures

### Key Features

- **Clojure format**: Used in Clojure applications
- **Extensible**: Supports custom types
- **Nested data**: Supports complex nested structures
- **Type preservation**: Maintains data types

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.edn') as source:
    for row in source:
        print(row)

# Writing
with open_iterable('output.edn', mode='w') as dest:
    dest.write({'name': 'John', 'age': 30})
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **Dependency**: Requires `edn_format` or `pyedn` package
2. **Clojure-specific**: Primarily used in Clojure ecosystem
3. **Less common**: Not as widely used as JSON
4. **Memory usage**: Entire file may be loaded into memory

## Compression Support

EDN files can be compressed with all supported codecs:
- GZip (`.edn.gz`)
- BZip2 (`.edn.bz2`)
- LZMA (`.edn.xz`)
- LZ4 (`.edn.lz4`)
- ZIP (`.edn.zip`)
- Brotli (`.edn.br`)
- ZStandard (`.edn.zst`)

## Use Cases

- **Clojure applications**: Data interchange in Clojure
- **Configuration**: Clojure-style configuration files
- **Data exchange**: Clojure-to-Python data exchange


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [JSON](json.md) - Similar structure
- [YAML](yaml.md) - Another configuration format
