# JSON-LD Format (JSON for Linking Data)

## Description

JSON-LD (JSON for Linking Data) is a method of encoding Linked Data using JSON. It's designed around the concept of a "context" to provide mappings from JSON to an RDF model. JSON-LD is particularly useful for representing structured data on the web and for data interchange between systems that need to preserve semantic meaning.

## File Extensions

- `.jsonld` - JSON-LD format

## Implementation Details

### Reading

The JSON-LD implementation supports multiple document structures:

1. **Line-by-line format** (JSONL-like): Each line is a complete JSON-LD object
2. **Array format**: A JSON array containing multiple JSON-LD objects
3. **Graph format**: A JSON-LD document with `@graph` containing multiple objects
4. **Single object**: A single JSON-LD object

The implementation automatically detects the format and handles:
- Extracting and preserving `@context` from document-level or object-level
- Handling `@graph` structures
- Preserving `@id` and other JSON-LD keywords
- Supporting nested structures

### Writing

Writing support:
- Writes each record as a single line (JSONL-like format)
- Automatically serializes datetime objects to ISO format
- Supports Unicode characters
- Preserves JSON-LD keywords like `@context`, `@id`, `@type`
- Efficient for bulk writes

### Key Features

- **Multiple format support**: Handles line-by-line, array, and graph formats
- **Context preservation**: Maintains `@context` information
- **Linked Data support**: Preserves semantic meaning through JSON-LD keywords
- **Nested data support**: Preserves complex nested structures
- **Totals support**: Can count total records in file
- **Datetime handling**: Automatically converts datetime objects to ISO format

## Usage

```python
from iterable import open_iterable

# Basic usage - line-by-line format
with open_iterable('data.jsonld') as source:
    for row in source:
        print(row)

# Reading array format
with open_iterable('data_array.jsonld') as source:
    for row in source:
        print(row['@id'], row['name'])

# Reading graph format
with open_iterable('data_graph.jsonld') as source:
    for row in source:
        print(row)

# Writing data
with open_iterable('output.jsonld', mode='w') as dest:
    dest.write({
        '@context': {'@vocab': 'http://example.org/'},
        '@id': 'person1',
        'name': 'John',
        'age': 30
    })
    dest.write({
        '@context': {'@vocab': 'http://example.org/'},
        '@id': 'person2',
        'name': 'Jane',
        'age': 25
    })

# Bulk writing
with open_iterable('output.jsonld', mode='w') as dest:
    records = [
        {'@context': {'@vocab': 'http://example.org/'}, '@id': '1', 'id': '1', 'value': 'a'},
        {'@context': {'@vocab': 'http://example.org/'}, '@id': '2', 'id': '2', 'value': 'b'}
    ]
    dest.write_bulk(records)
```

## JSON-LD Structure

JSON-LD documents can have several structures:

### Line-by-line format
```json
{"@context": {"@vocab": "http://example.org/"}, "@id": "1", "name": "John"}
{"@context": {"@vocab": "http://example.org/"}, "@id": "2", "name": "Jane"}
```

### Array format
```json
[
  {"@context": {"@vocab": "http://example.org/"}, "@id": "1", "name": "John"},
  {"@context": {"@vocab": "http://example.org/"}, "@id": "2", "name": "Jane"}
]
```

### Graph format
```json
{
  "@context": {"@vocab": "http://example.org/"},
  "@graph": [
    {"@id": "1", "name": "John"},
    {"@id": "2", "name": "Jane"}
  ]
}
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## JSON-LD Keywords

The implementation preserves standard JSON-LD keywords:
- `@context`: Defines the mapping from JSON to RDF
- `@id`: Identifies the subject of a JSON-LD object
- `@type`: Specifies the type of a node
- `@value`: The actual value of a property
- `@language`: The language of a string value
- `@graph`: Contains a set of nodes

## Limitations

1. **Context handling**: Document-level `@context` is preserved but not expanded
2. **No expansion/compaction**: The implementation does not perform JSON-LD expansion or compaction
3. **No validation**: Invalid JSON-LD will cause parsing errors
4. **Writing format**: Always writes in line-by-line format (one JSON-LD object per line)

## Compression Support

JSON-LD files can be compressed with all supported codecs:
- GZip (`.jsonld.gz`)
- BZip2 (`.jsonld.bz2`)
- LZMA (`.jsonld.xz`)
- LZ4 (`.jsonld.lz4`)
- ZIP (`.jsonld.zip`)
- Brotli (`.jsonld.br`)
- ZStandard (`.jsonld.zst`)

## Use Cases

- **Linked Data**: Representing structured data with semantic meaning
- **Web APIs**: Exchanging structured data between systems
- **Knowledge graphs**: Storing and processing graph data
- **Schema.org data**: Representing structured data for search engines
- **RDF data**: Converting between RDF and JSON formats

## Related Formats

- [JSON](json.md) - For reading array-based JSON files
- [JSONL](jsonl.md) - For line-by-line JSON format
- [RDF/XML](rdfxml.md) - For RDF data in XML format
- [Turtle](turtle.md) - For RDF data in Turtle format
