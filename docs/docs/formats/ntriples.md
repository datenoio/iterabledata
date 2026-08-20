# N-Triples Format (RDF)

## Description

N-Triples is a simple, line-based format for representing RDF (Resource Description Framework) data. Each line represents a single RDF triple (subject-predicate-object). It's one of the simplest RDF serialization formats.

## File Extensions

- `.nt` - N-Triples files
- `.ntriples` - N-Triples files (alias)

## Implementation Details

### Reading

The N-Triples implementation:
- Parses N-Triples format line by line
- Extracts subject, predicate, and object from each line
- Handles URIs and literals
- Converts each triple to a dictionary
- Supports streaming for large files

### Writing

Writing is not currently supported for N-Triples format.

### Key Features

- **Line-based**: One triple per line
- **Simple format**: Easy to parse and generate
- **RDF format**: Represents RDF data
- **Totals support**: Can count total triples
- **Streaming**: Processes files line by line

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.nt') as source:
    for row in source:
        print(row)  # Contains: subject, predicate, object
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## N-Triples Format Structure

Format: `subject predicate object .`

- **subject**: URI or blank node
- **predicate**: URI
- **object**: URI, literal, or blank node
- **period**: Ends each triple

## Limitations

1. **Read-only**: N-Triples format does not support writing
2. **Line-based format**: Each triple must fit on a single line
3. **No abbreviations**: More verbose than Turtle
4. **Flat structure**: Each triple is separate (no grouping)

## Compression Support

N-Triples files can be compressed with all supported codecs:
- GZip (`.nt.gz`)
- BZip2 (`.nt.bz2`)
- LZMA (`.nt.xz`)
- LZ4 (`.nt.lz4`)
- ZIP (`.nt.zip`)
- Brotli (`.nt.br`)
- ZStandard (`.nt.zst`)

## Use Cases

- **RDF data**: Working with RDF datasets
- **Linked data**: Processing linked data
- **Knowledge graphs**: Building knowledge graphs
- **Data exchange**: Simple RDF data exchange

## Related Formats

- [N-Quads](nquads.md) - N-Triples with graph context
- [Turtle](turtle.md) - More compact RDF format
- [RDF/XML](rdfxml.md) - RDF in XML format
