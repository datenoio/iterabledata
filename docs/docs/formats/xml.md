# XML Format

## Description

XML (eXtensible Markup Language) is a markup language for storing and transporting data. XML supports hierarchical/nested data structures and is widely used for data exchange. The XML implementation in Iterable Data parses XML files and extracts records based on a specified tag name.

## File Extensions

- `.xml` - Standard XML files

## Implementation Details

### Reading

The XML implementation:
- Uses `lxml` library for parsing
- Supports iterative parsing for large files
- Extracts records based on a specified tag name
- Converts XML elements to dictionaries
- Handles attributes and text content
- Supports namespace prefix stripping

### Writing

Writing is not currently supported for XML format.

### Key Features

- **Tag-based extraction**: Extracts records matching a specific XML tag
- **Namespace handling**: Can strip XML namespace prefixes
- **Attribute support**: XML attributes are included in records (prefixed with `@`)
- **Text content**: Element text is included (key: `#text`)
- **Iterative parsing**: Processes large files efficiently
- **Error recovery**: Handles malformed XML with recovery mode

## Usage

```python
from iterable import open_iterable

# Recommended: Using context manager (automatic cleanup)
# Basic usage - specify tag name
with open_iterable('data.xml', iterableargs={
    'tagname': 'book'  # Extract all <book> elements
}) as source:
    for row in source:
        print(row)
# File automatically closed

# With namespace prefix stripping
with open_iterable('data.xml', iterableargs={
    'tagname': 'item',
    'prefix_strip': True  # Strip namespace prefixes
}) as source:
    for row in source:
        print(row)

# Alternative: Manual close (still supported)
source = open_iterable('data.xml', iterableargs={'tagname': 'book'})
try:
    for row in source:
        print(row)
finally:
    source.close()
```

### Discovering Available Tags

XML files can contain multiple tag types. Use `list_tables()` to discover available tag names:

```python
from iterable.datatypes.xml import XMLIterable

# Before opening - discover tag names
iterable = XMLIterable('data.xml')
tag_names = iterable.list_tables('data.xml')
print(f"Available tags: {tag_names}")

# After opening - list all tags (reuses open file)
source = open_iterable('data.xml', iterableargs={'tagname': 'book'})
all_tags = source.list_tables()  # Reuses open file handle
print(f"All tags: {all_tags}")

# Process different tag types
for tag_name in all_tags:
    source = open_iterable('data.xml', iterableargs={'tagname': tag_name})
    print(f"Processing tag: {tag_name}")
    for row in source:
        process(row)
    source.close()
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `tagname` | str | None | **Yes** | XML tag name to extract records from. All elements matching this tag will be converted to records. |
| `prefix_strip` | bool | `True` | No | Strip XML namespace prefixes from element and attribute names. Set to `False` to preserve namespace prefixes. |

## XML Structure

The XML parser converts XML elements to dictionaries:

```xml
<book id="123" category="fiction">
    <title>Example Book</title>
    <author>John Doe</author>
</book>
```

Becomes:
```python
{
    'title': 'Example Book',
    'author': 'John Doe',
    '@id': '123',
    '@category': 'fiction'
}
```

## Error Handling

```python
from iterable import open_iterable

try:
    # Reading with error handling
    with open_iterable('data.xml', iterableargs={
        'tagname': 'book'
    }) as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("XML file not found")
except ValueError as e:
    if "tagname" in str(e).lower():
        print("tagname parameter is required for XML files")
    else:
        print(f"Value error: {e}")
except Exception as e:
    print(f"Error reading XML: {e}")
    # XML parsing errors may indicate malformed XML
```

### Common Errors

- **"tagname parameter is required"**: Must provide `tagname` parameter when reading XML files
- **XML parsing errors**: May indicate malformed XML - check file format
- **Memory errors**: Very large XML files may require more memory - consider processing in chunks
- **Missing lxml**: Install `lxml` package: `pip install lxml`

## Limitations

1. **Read-only**: XML format does not support writing
2. **Tag name required**: Must specify the tag name to extract
3. **Memory for large files**: Uses iterative parsing but may still use significant memory
4. **Complex structures**: Very deeply nested structures may be difficult to work with
5. **Namespace complexity**: Complex namespaces may require manual handling
6. **lxml dependency**: Requires `lxml` package

## Compression Support

XML files can be compressed with all supported codecs:
- GZip (`.xml.gz`)
- BZip2 (`.xml.bz2`)
- LZMA (`.xml.xz`)
- LZ4 (`.xml.lz4`)
- ZIP (`.xml.zip`)
- Brotli (`.xml.br`)
- ZStandard (`.xml.zst`)

## Performance Considerations

### Performance Tips

- **Iterative parsing**: XML files are processed iteratively, making them memory-efficient for large files
- **Tag selection**: Only elements matching the specified tag are processed, improving performance
- **Compression**: Compressed XML files (`.xml.gz`, `.xml.zst`) can be processed efficiently
- **Memory usage**: Very large XML files may still use significant memory - monitor memory usage for files > 1GB
- **Namespace handling**: Stripping namespace prefixes (`prefix_strip=True`) is faster than preserving them

## Use Cases

- **Data exchange**: Interfacing with XML-based APIs
- **Legacy systems**: Working with older XML-based data formats
- **Document processing**: Processing structured documents
- **Web scraping**: Parsing XML responses

## Related Formats

- [RDF/XML](rdfxml.md) - RDF data in XML format
- [WARC](warc.md) - Web archive format (may contain XML)
