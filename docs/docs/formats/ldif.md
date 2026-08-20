# LDIF Format (LDAP Data Interchange Format)

## Description

LDIF (LDAP Data Interchange Format) is a text format for representing LDAP (Lightweight Directory Access Protocol) directory entries. It's used for importing and exporting directory data, and is commonly used with LDAP servers.

## File Extensions

- `.ldif` - LDIF format files

## Implementation Details

### Reading

The LDIF implementation:
- Uses `ldif3` or `ldif` library for parsing
- Parses LDIF format line by line
- Extracts directory entries (DN and attributes)
- Handles continuation lines
- Converts each entry to a dictionary
- Supports streaming for large files

### Writing

Writing is not currently supported for LDIF format.

### Key Features

- **Directory format**: Designed for LDAP directory data
- **Entry-based**: Each entry represents a directory object
- **Attribute extraction**: Extracts LDAP attributes
- **Totals support**: Can count total entries
- **Streaming**: Processes files line by line

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('directory.ldif') as source:
    for entry in source:
        print(entry)  # Contains DN and attributes
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## LDIF Format Structure

LDIF entries consist of:
- **DN**: Distinguished Name (entry identifier)
- **Attributes**: Key-value pairs (attribute: value)
- **Continuation lines**: Lines starting with space continue previous attribute

## Limitations

1. **Read-only**: LDIF format does not support writing
2. **Dependency**: Requires `ldif3` or `ldif` package
3. **LDAP focus**: Designed for LDAP directory data
4. **Format complexity**: Complex LDAP structures may require manual handling

## Compression Support

LDIF files can be compressed with all supported codecs:
- GZip (`.ldif.gz`)
- BZip2 (`.ldif.bz2`)
- LZMA (`.ldif.xz`)
- LZ4 (`.ldif.lz4`)
- ZIP (`.ldif.zip`)
- Brotli (`.ldif.br`)
- ZStandard (`.ldif.zst`)

## Use Cases

- **LDAP directories**: Working with LDAP directory data
- **User management**: Managing user directory data
- **Data migration**: Migrating directory data
- **Directory sync**: Synchronizing directory data

## Related Formats

- [CSV](csv.md) - Simple text format
- [JSON](json.md) - Structured format
