# VCF Format (vCard)

## Description

VCF (vCard) is a standard format (RFC 6350) for electronic business cards. It's used to represent contact information and is supported by most email clients and address book applications. VCF files contain contact details like name, email, phone, address, etc.

## File Extensions

- `.vcf` - vCard files
- `.vcard` - vCard files (alias)

## Implementation Details

### Reading

The VCF implementation:
- Uses `vobject` or `vcard` library for parsing
- Parses vCard format
- Extracts contact information
- Converts each vCard to a dictionary
- Handles vCard properties and attributes

### Writing

Writing is supported: `write()` and `write_bulk()` serialize record dictionaries
back to vCard entries (requires the `vobject` package).

### Key Features

- **Contact format**: Designed for contact information
- **Standard format**: RFC 6350 standard
- **Contact extraction**: Extracts contact details
- **Nested data**: Supports complex contact structures
- **Multiple contacts**: Can contain multiple vCards

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('contacts.vcf') as source:
    for contact in source:
        print(contact)  # Contains contact information
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **Dependency**: Requires `vobject` or `vcard` package (install with `pip install iterabledata[vcf]`)
2. **Contact focus**: Designed for contact data, not general data
3. **Format complexity**: Complex vCard structures may require manual handling

## Compression Support

VCF files can be compressed with all supported codecs:
- GZip (`.vcf.gz`)
- BZip2 (`.vcf.bz2`)
- LZMA (`.vcf.xz`)
- LZ4 (`.vcf.lz4`)
- ZIP (`.vcf.zip`)
- Brotli (`.vcf.br`)
- ZStandard (`.vcf.zst`)

## Use Cases

- **Contact management**: Working with contact information
- **Address books**: Processing address book data
- **Data migration**: Migrating contact data
- **Email clients**: Importing/exporting contacts

## Related Formats

- [iCal](ical.md) - iCalendar format
- [EML](eml.md) - Email format
