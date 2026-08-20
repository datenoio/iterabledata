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

Writing support:
- Writes each record as `key = value` HOCON assignments
- `write_bulk()` emits a HOCON array of objects
- Requires `pip install iterabledata[hocon]` (`pyhocon`)

### Key Features

- **Human-friendly**: More readable than JSON
- **JSON superset**: Extends JSON with additional features
- **Configuration format**: Designed for configuration files
- **Nested data**: Supports complex nested structures

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('config.hocon') as source:
    for row in source:
        print(row)  # Configuration entries

# Writing
with open_iterable('output.hocon', mode='w') as dest:
    dest.write({'host': 'localhost', 'port': 8080})
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **HOCON extra**: Requires `pip install iterabledata[hocon]` (`pyhocon`)
2. **Configuration focus**: Designed for configuration, not general data
3. **Memory usage**: Entire file is loaded into memory

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
