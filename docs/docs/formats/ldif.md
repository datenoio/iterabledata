# LDIF Format (LDAP Data Interchange Format)

## Description

LDIF (LDAP Data Interchange Format) is a text format for representing LDAP (Lightweight Directory Access Protocol) directory entries. It's used for importing and exporting directory data, and is commonly used with LDAP servers.

## File Extensions

- `.ldif` - LDIF format files

## Implementation Details

### Reading

The LDIF implementation:
- Uses `ldif3` for parsing (`pip install iterabledata[ldif]`)
- Parses LDIF format line by line
- Extracts directory entries (DN and attributes)
- Handles continuation lines
- Converts each entry to a dictionary
- Supports streaming for large files

### Writing

Writing support:
- Requires a `dn` field on each record
- Writes attributes as `key: value` lines
- Install with `pip install iterabledata[ldif]` (`ldif3`)

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

# Writing
with open_iterable('output.ldif', mode='w') as dest:
    dest.write({'dn': 'cn=Ada,dc=example,dc=org', 'cn': 'Ada', 'mail': 'ada@example.org'})
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## LDIF Format Structure

LDIF entries consist of:
- **DN**: Distinguished Name (entry identifier)
- **Attributes**: Key-value pairs (attribute: value)
- **Continuation lines**: Lines starting with space continue previous attribute

## Limitations

1. **LDIF extra**: Requires `pip install iterabledata[ldif]` (`ldif3`)
2. **LDAP focus**: Designed for LDAP directory data
3. **Format complexity**: Complex LDAP structures may require manual handling

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


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [CSV](csv.md) - Simple text format
- [JSON](json.md) - Structured format
