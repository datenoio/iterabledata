# INI Format

## Description

INI (Initialization) format is a simple configuration file format used for storing application settings. It supports sections (marked with `[section]`) and key-value pairs. The format is also used for properties files (without sections).

## File Extensions

- `.ini` - INI configuration files
- `.properties` - Properties files (alias)
- `.conf` - Configuration files (alias)

## Implementation Details

### Reading

The INI implementation:
- Uses Python's `configparser` module
- Supports sections and key-value pairs
- Handles properties files (no sections)
- Converts sections to records with `_section` field
- Falls back to simple key=value parsing if configparser fails

### Writing

Writing support:
- Writes INI format with sections
- Supports key-value pairs
- Can write properties format (no sections)

### Key Features

- **Section support**: Handles INI sections
- **Properties format**: Also supports properties files
- **Simple format**: Easy to read and write
- **Configuration files**: Designed for application configuration

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('config.ini') as source:
    for row in source:
        print(row)  # Each row has _section and key-value pairs

# Writing
with open_iterable('output.ini', mode='w') as dest:
    dest.write({'_section': 'database', 'host': 'localhost', 'port': '5432'})
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **Simple format**: Limited to key-value pairs
2. **No nested structures**: Doesn't support complex nested data
3. **Type handling**: All values are strings
4. **Section handling**: Sections are converted to `_section` field

## Compression Support

INI files can be compressed with all supported codecs:
- GZip (`.ini.gz`)
- BZip2 (`.ini.bz2`)
- LZMA (`.ini.xz`)
- LZ4 (`.ini.lz4`)
- ZIP (`.ini.zip`)
- Brotli (`.ini.br`)
- ZStandard (`.ini.zst`)

## Use Cases

- **Configuration files**: Application and system configuration
- **Properties files**: Java-style properties files
- **Settings storage**: Storing application settings
- **Simple config**: When you need simple key-value configuration

## Related Formats

- [TOML](toml.md) - More advanced configuration format
- [YAML](yaml.md) - Another configuration format
- [JSON](json.md) - Structured configuration format
