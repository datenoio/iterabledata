# RDF/XML Format

## Description

RDF/XML is an XML-based serialization format for RDF (Resource Description Framework) data. It represents RDF triples (subject-predicate-object) in XML format. RDF/XML is one of the standard RDF serialization formats.

## File Extensions

- `.rdf` - RDF/XML files
- `.rdf.xml` - RDF/XML files (alias)

## Implementation Details

### Reading

The RDF/XML implementation:
- Uses `lxml` library for XML parsing
- Parses RDF Description elements
- Extracts RDF triples (subject-predicate-object)
- Groups triples by subject
- Converts RDF data to dictionaries

### Writing

Writing support:
- Writes RDF `Description` elements (simplified RDF/XML)
- Triple-oriented records use `subject` plus a `triples` list

### Key Features

- **RDF format**: Represents RDF data in XML
- **Triple extraction**: Extracts RDF triples
- **Subject grouping**: Groups triples by subject
- **Nested data**: Supports complex RDF structures
- **XML parsing**: Uses XML parsing for RDF data

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.rdf') as source:
    for row in source:
        print(row)  # Contains RDF triples grouped by subject

# Writing
with open_iterable('output.rdf', mode='w') as dest:
    dest.write({'subject': 'http://example.org/alice', 'name': 'Alice'})
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **lxml dependency**: Requires `lxml` package
2. **Memory usage**: Entire RDF graph may be loaded into memory
3. **RDF complexity**: Complex RDF structures may be difficult to work with
4. **XML complexity**: Complex XML namespaces may require manual handling

## Compression Support

RDF/XML files can be compressed with all supported codecs:
- GZip (`.rdf.gz`)
- BZip2 (`.rdf.bz2`)
- LZMA (`.rdf.xz`)
- LZ4 (`.rdf.lz4`)
- ZIP (`.rdf.zip`)
- Brotli (`.rdf.br`)
- ZStandard (`.rdf.zst`)

## Use Cases

- **Semantic web**: Working with semantic web data
- **Linked data**: Processing linked data
- **Knowledge graphs**: Building and querying knowledge graphs
- **Metadata**: Working with RDF metadata


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [Turtle](turtle.md) - More readable RDF format
- [N-Triples](ntriples.md) - Simpler RDF format
- [N-Quads](nquads.md) - N-Triples with graph context
- [XML](xml.md) - Base XML format
