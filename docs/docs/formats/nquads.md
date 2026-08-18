# N-Quads Format (RDF)

## Description

N-Quads is an extension of N-Triples that adds a fourth element (graph context) to each triple. It's used to represent RDF datasets with named graphs. Each line represents a single RDF quad (subject-predicate-object-graph).

## File Extensions

- `.nq` - N-Quads files
- `.nquads` - N-Quads files (alias)

## Implementation Details

### Reading

The N-Quads implementation:
- Extends N-Triples implementation
- Parses N-Quads format line by line
- Extracts subject, predicate, object, and graph from each line
- Converts each quad to a dictionary
- Supports streaming for large files

### Writing

Writing is not currently supported for N-Quads format.

### Key Features

- **Line-based**: One quad per line
- **Graph context**: Includes graph identifier
- **RDF dataset**: Represents RDF datasets with named graphs
- **Totals support**: Can count total quads
- **Streaming**: Processes files line by line

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('data.nq')
for row in source:
    print(row)  # Contains: subject, predicate, object, graph
source.close()
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## N-Quads Format Structure

Format: `subject predicate object graph .`

- **subject**: URI or blank node
- **predicate**: URI
- **object**: URI, literal, or blank node
- **graph**: Graph identifier (URI or blank node)
- **period**: Ends each quad

## Limitations

1. **Read-only**: N-Quads format does not support writing
2. **Line-based format**: Each quad must fit on a single line
3. **No abbreviations**: More verbose than Turtle
4. **Flat structure**: Each quad is separate (no grouping)

## Compression Support

N-Quads files can be compressed with all supported codecs:
- GZip (`.nq.gz`)
- BZip2 (`.nq.bz2`)
- LZMA (`.nq.xz`)
- LZ4 (`.nq.lz4`)
- ZIP (`.nq.zip`)
- Brotli (`.nq.br`)
- ZStandard (`.nq.zst`)

## Use Cases

- **RDF datasets**: Working with RDF datasets with named graphs
- **Linked data**: Processing linked data with graph context
- **Knowledge graphs**: Building knowledge graphs with multiple graphs
- **Data exchange**: RDF dataset exchange

## Related Formats

- [N-Triples](ntriples.md) - Simpler format without graph context
- [Turtle](turtle.md) - More compact RDF format
- [RDF/XML](rdfxml.md) - RDF in XML format
