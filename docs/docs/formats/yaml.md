# YAML Format

## Description

YAML (YAML Ain't Markup Language) is a human-readable data serialization format. It's commonly used for configuration files and data exchange. YAML supports complex nested data structures and is more readable than JSON for human editing.

## File Extensions

- `.yaml` - YAML files
- `.yml` - YAML files (alias)

## Implementation Details

### Reading

The YAML implementation:
- Uses `pyyaml` library for parsing
- Supports multiple YAML documents (separated by `---`)
- Handles lists and dictionaries
- Converts YAML documents to Python objects

### Writing

Writing support:
- Writes each record as a separate YAML document
- Separates documents with `---`
- Supports Unicode characters
- Uses block style (not flow style) for readability

### Key Features

- **Multiple documents**: Supports YAML files with multiple documents
- **Nested data**: Supports complex nested structures
- **Human-readable**: Easy to read and edit
- **Unicode support**: Full Unicode character support

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.yaml') as source:
    for row in source:
        print(row)

# Writing
with open_iterable('output.yaml', mode='w') as dest:
    dest.write({'name': 'John', 'age': 30})
    dest.write({'name': 'Jane', 'age': 25})
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `encoding` | str | `utf8` | No | File encoding for reading/writing YAML files. Common values: `utf-8`, `latin-1`, `cp1252`. |

## Error Handling

```python
from iterable import open_iterable
import yaml

try:
    # Reading with error handling
    with open_iterable('data.yaml') as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("YAML file not found")
except yaml.YAMLError as e:
    print(f"YAML parsing error: {e}")
    if hasattr(e, "problem_mark"):
        mark = e.problem_mark
        print(f"Error position: line {mark.line + 1}, column {mark.column + 1}")
except UnicodeDecodeError:
    print("Encoding error - try specifying encoding explicitly")
    with open_iterable('data.yaml', iterableargs={'encoding': 'latin-1'}) as source:
        for row in source:
            process(row)
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install iterabledata[yaml] or pip install pyyaml")
except Exception as e:
    print(f"Error reading YAML: {e}")

try:
    # Writing with error handling
    with open_iterable('output.yaml', mode='w') as dest:
        dest.write({'name': 'John', 'age': 30})
except Exception as e:
    print(f"Error writing YAML: {e}")
```

### Common Errors

- **YAMLError**: Invalid YAML syntax - check file format and indentation
- **UnicodeDecodeError**: Encoding issue - specify correct encoding
- **ImportError**: Missing `pyyaml` package - install with `pip install pyyaml`
- **FileNotFoundError**: File path is incorrect or file doesn't exist

## Limitations

1. **pyyaml dependency**: Requires `pyyaml` package
2. **Memory usage**: Multiple documents are loaded into memory
3. **Performance**: Slower than binary formats
4. **Write format**: Each record written as separate document with `---` separator

## Compression Support

YAML files can be compressed with all supported codecs:
- GZip (`.yaml.gz`)
- BZip2 (`.yaml.bz2`)
- LZMA (`.yaml.xz`)
- LZ4 (`.yaml.lz4`)
- ZIP (`.yaml.zip`)
- Brotli (`.yaml.br`)
- ZStandard (`.yaml.zst`)

## Use Cases

- **Configuration files**: Application and system configuration
- **Data exchange**: Human-readable data format
- **Documentation**: Embedding data in documentation
- **DevOps**: Infrastructure as code (Ansible, Kubernetes)

## Related Formats

- [JSON](json.md) - Similar structure, less readable
- [TOML](toml.md) - Another configuration format
- [INI](ini.md) - Simpler configuration format
