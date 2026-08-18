# ASN.1 Format

## Description

ASN.1 (Abstract Syntax Notation One) is a standard interface description language for defining data structures. It's widely used in telecommunications and cryptography. ASN.1 data can be encoded in various formats, with DER (Distinguished Encoding Rules) being common.

## File Extensions

- `.asn1` - ASN.1 files
- `.der` - DER-encoded ASN.1 files (alias)

## Implementation Details

### Reading

The ASN.1 implementation:
- Uses `pyasn1` library for decoding
- Parses DER-encoded ASN.1 data
- Converts ASN.1 structures to Python dictionaries
- Handles sequences and other ASN.1 types

### Writing

Writing support:
- Encodes Python dictionaries to ASN.1 format
- Writes DER-encoded ASN.1 data
- Note: Simplified conversion, real ASN.1 encoding requires schema

### Key Features

- **Standard format**: ITU-T and ISO standard
- **Telecommunications**: Widely used in telecom
- **Cryptography**: Used in certificates and keys
- **Binary format**: DER encoding is binary
- **Schema-based**: Typically requires ASN.1 schema

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('data.der')
for row in source:
    print(row)
source.close()

# Writing
dest = open_iterable('output.der', mode='w')
dest.write({'field1': 'value1', 'field2': 123})
dest.close()
```

## Parameters

No specific parameters required.

## Limitations

1. **pyasn1 dependency**: Requires `pyasn1` package
2. **Schema complexity**: Real ASN.1 encoding requires schema
3. **Binary format**: Not human-readable
4. **Simplified conversion**: Current implementation is simplified
5. **DER encoding**: Primarily supports DER encoding

## Compression Support

ASN.1 files can be compressed with all supported codecs:
- GZip (`.der.gz`)
- BZip2 (`.der.bz2`)
- LZMA (`.der.xz`)
- LZ4 (`.der.lz4`)
- ZIP (`.der.zip`)
- Brotli (`.der.br`)
- ZStandard (`.der.zst`)

## Use Cases

- **Telecommunications**: Telecom protocol data
- **Cryptography**: Certificates, keys, and cryptographic data
- **Standards compliance**: When ASN.1 is required by standards
- **X.509 certificates**: Certificate encoding

## Related Formats

- [Protocol Buffers](protobuf.md) - Similar schema-based format
- [Thrift](thrift.md) - Another serialization format
