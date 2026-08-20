# Turtle Format (RDF)

## Description

Turtle is a text-based format for representing RDF (Resource Description Framework) data. It's a human-readable serialization of RDF graphs. Turtle files represent RDF triples (subject-predicate-object) in a compact, readable format.

## File Extensions

- `.ttl` - Turtle RDF files
- `.turtle` - Turtle RDF files (alias)

## Implementation Details

### Reading

The Turtle implementation:
- Uses `rdflib` library for parsing
- Parses RDF triples from Turtle format
- Groups triples by subject
- Converts each subject to a dictionary with its properties
- Supports optional subject/predicate filtering

### Writing

Writing is not currently supported for Turtle format.

### Key Features

- **RDF format**: Represents RDF data
- **Human-readable**: More readable than RDF/XML
- **Triple grouping**: Groups triples by subject
- **Nested data**: Supports complex RDF structures
- **Filtering**: Can filter by subject or predicate

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.ttl') as source:
    for row in source:
        print(row)  # Each row represents a subject with its properties

# Filter by subject
source = open_iterable('data.ttl', iterableargs={
    'subject': 'http://example.org/person1'
})
```

## Parameters

- `subject` (str): Optional - Filter by subject URI
- `predicate` (str): Optional - Filter by predicate URI
- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **Read-only**: Turtle format does not support writing
2. **rdflib dependency**: Requires `rdflib` package
3. **Memory usage**: Entire RDF graph is loaded into memory
4. **RDF complexity**: Complex RDF structures may be difficult to work with
5. **Triple grouping**: Triples are grouped by subject, which may not match all use cases

## Compression Support

Turtle files can be compressed with all supported codecs:
- GZip (`.ttl.gz`)
- BZip2 (`.ttl.bz2`)
- LZMA (`.ttl.xz`)
- LZ4 (`.ttl.lz4`)
- ZIP (`.ttl.zip`)
- Brotli (`.ttl.br`)
- ZStandard (`.ttl.zst`)

## Use Cases

- **Semantic web**: Working with semantic web data
- **Linked data**: Processing linked data
- **Knowledge graphs**: Building and querying knowledge graphs
- **Metadata**: Working with RDF metadata

## Related Formats

- [N-Triples](ntriples.md) - Simpler RDF format
- [N-Quads](nquads.md) - N-Triples with graph context
- [RDF/XML](rdfxml.md) - RDF in XML format
