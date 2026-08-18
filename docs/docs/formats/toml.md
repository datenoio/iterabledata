# TOML Format

## Description

TOML (Tom's Obvious, Minimal Language) is a configuration file format designed to be easy to read and write. It's used by many modern tools and projects for configuration files. TOML supports nested data structures, arrays, and tables.

## File Extensions

- `.toml` - TOML files

## Implementation Details

### Reading

The TOML implementation:
- Uses `tomli` (or `toml`) library for parsing
- Supports array of tables (common TOML pattern)
- Converts TOML structures to Python dictionaries
- Handles nested tables and arrays

### Writing

Writing support:
- Uses `tomli-w` (or `toml`) for writing
- Writes TOML format
- Supports nested structures

### Key Features

- **Nested data**: Supports complex nested structures
- **Array of tables**: Handles TOML's array of tables pattern
- **Human-readable**: Easy to read and edit
- **Configuration format**: Designed for configuration files

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('config.toml')
for row in source:
    print(row)
source.close()

# Writing
dest = open_iterable('output.toml', mode='w')
dest.write({'name': 'John', 'age': 30})
dest.close()
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `encoding` | str | `utf8` | No | File encoding for reading/writing TOML files. Common values: `utf-8`, `latin-1`, `cp1252`. |

## Error Handling

```python
from iterable import open_iterable

try:
    # Reading with error handling
    with open_iterable('config.toml') as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("TOML file not found")
except Exception as e:
    # TOML parsing errors vary by library
    print(f"TOML parsing error: {e}")
    # Common causes: invalid syntax, type mismatches, duplicate keys
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install iterabledata[toml] or pip install tomli")
except Exception as e:
    print(f"Error reading TOML: {e}")

try:
    # Writing with error handling
    with open_iterable('output.toml', mode='w') as dest:
        dest.write({'name': 'John', 'age': 30})
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install iterabledata[toml] or pip install tomli-w")
except Exception as e:
    print(f"Error writing TOML: {e}")
```

### Common Errors

- **TOML parsing errors**: Invalid TOML syntax - check file format and structure
- **ImportError**: Missing `tomli`/`tomli-w` or `toml` package - install with `pip install tomli` or `pip install tomli-w`
- **FileNotFoundError**: File path is incorrect or file doesn't exist

## Limitations

1. **Dependency**: Requires `tomli`/`tomli-w` or `toml` package
2. **⚠️ Memory usage**: **Entire TOML file is loaded into memory** before processing. For large files (>100MB), consider:
   - Converting to JSONL or CSV format first
   - Using streaming formats for large configuration files
   - Splitting large TOML files into smaller files
3. **Structure complexity**: Complex nested structures may be difficult to iterate
4. **Array of tables**: TOML's array of tables pattern may require specific structure

## Compression Support

TOML files can be compressed with all supported codecs:
- GZip (`.toml.gz`)
- BZip2 (`.toml.bz2`)
- LZMA (`.toml.xz`)
- LZ4 (`.toml.lz4`)
- ZIP (`.toml.zip`)
- Brotli (`.toml.br`)
- ZStandard (`.toml.zst`)

## Use Cases

- **Configuration files**: Application and tool configuration
- **Project settings**: Project configuration files
- **Data exchange**: Human-readable data format

## Related Formats

- [YAML](yaml.md) - Another configuration format
- [INI](ini.md) - Simpler configuration format
- [JSON](json.md) - Similar structure, less readable
