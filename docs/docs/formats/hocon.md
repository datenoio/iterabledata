# HOCON Format (Human-Optimized Config Object Notation)

## Description

HOCON (Human-Optimized Config Object Notation) is a configuration file format developed by Lightbend (formerly Typesafe) for use with their products like Play Framework and Akka. It's a superset of JSON and is designed to be more human-friendly.

## File Extensions

- `.hocon` - HOCON configuration files

## Implementation Details

### Reading

The HOCON implementation:
- Uses `pyhocon` library for parsing
- Parses HOCON configuration files
- Converts HOCON structures to Python dictionaries
- Handles arrays and nested objects
- Groups configuration by keys

### Writing

Writing is not currently supported for HOCON format.

### Key Features

- **Human-friendly**: More readable than JSON
- **JSON superset**: Extends JSON with additional features
- **Configuration format**: Designed for configuration files
- **Nested data**: Supports complex nested structures

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('config.hocon')
for row in source:
    print(row)  # Configuration entries
source.close()
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **Read-only**: HOCON format does not support writing
2. **pyhocon dependency**: Requires `pyhocon` package
3. **Configuration focus**: Designed for configuration, not general data
4. **Memory usage**: Entire file is loaded into memory

## Compression Support

HOCON files can be compressed with all supported codecs:
- GZip (`.hocon.gz`)
- BZip2 (`.hocon.bz2`)
- LZMA (`.hocon.xz`)
- LZ4 (`.hocon.lz4`)
- ZIP (`.hocon.zip`)
- Brotli (`.hocon.br`)
- ZStandard (`.hocon.zst`)

## Use Cases

- **Play Framework**: Configuration for Play applications
- **Akka**: Configuration for Akka systems
- **Configuration files**: Human-friendly configuration
- **Lightbend products**: Products from Lightbend/Typesafe

## Related Formats

- [JSON](json.md) - Base format that HOCON extends
- [YAML](yaml.md) - Another configuration format
- [TOML](toml.md) - Another configuration format
