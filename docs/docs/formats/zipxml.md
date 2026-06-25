# ZIPXML Format

## Description

ZIPXML is a format for reading XML files stored within ZIP archives. This is useful when working with archives containing multiple XML files, such as data exports, document archives, or bulk XML data. The ZIPXML implementation allows you to iterate through XML files within a ZIP archive and extract records based on XML tag names.

## File Extensions

- `.zip` - ZIP archives containing XML files (when used with ZIPXML format)

## Implementation Details

### Reading

The ZIPXML implementation:
- Uses Python's `zipfile` library for ZIP handling
- Uses `lxml` library for XML parsing
- Iterates through XML files within the ZIP archive
- Extracts records based on specified tag names
- Supports multiple XML files per archive
- Processes files sequentially

### Writing

Writing is not currently supported for ZIPXML format.

### Key Features

- **Multiple XML files**: Can process multiple XML files within a single ZIP archive
- **Tag-based extraction**: Extracts records matching a specific XML tag
- **File iteration**: Automatically iterates through all XML files in the archive
- **Table listing**: Can list all XML files within the ZIP archive
- **Namespace handling**: Supports XML namespace prefix stripping

## Usage

```python
from iterable.helpers.detect import open_iterable

# Recommended: Using context manager (automatic cleanup)
# Basic reading - iterate through all XML files
with open_iterable('archive.zip', iterableargs={
    'tagname': 'item'  # Extract all <item> elements from all XML files
}) as source:
    for row in source:
        print(row)
# File automatically closed

# Discover available XML files
from iterable.datatypes.zipxml import ZIPXMLSource

# Before opening - discover XML files
iterable = ZIPXMLSource('archive.zip', tagname='item')
xml_files = iterable.list_tables('archive.zip')
print(f"Available XML files: {xml_files}")

# After opening - list all XML files (reuses open ZIP)
source = open_iterable('archive.zip', iterableargs={'tagname': 'item'})
all_files = source.list_tables()  # Reuses open ZIP handle
print(f"All XML files: {all_files}")

# Process specific XML files
for xml_file in all_files:
    # Note: ZIPXML processes files sequentially, not individually
    # To process specific files, you may need to extract them first
    print(f"Processing file: {xml_file}")

# Alternative: Manual close (still supported)
source = open_iterable('archive.zip', iterableargs={'tagname': 'item'})
try:
    for row in source:
        print(row)
finally:
    source.close()
```

### Discovering Available XML Files

ZIP archives can contain multiple XML files. Use `list_tables()` to discover available XML files:

```python
from iterable.datatypes.zipxml import ZIPXMLSource

# Before opening - discover XML files
iterable = ZIPXMLSource('archive.zip', tagname='item')
xml_files = iterable.list_tables('archive.zip')
print(f"Available XML files: {xml_files}")
# Output: ['data1.xml', 'data2.xml', 'records.xml']

# After opening - list all XML files (reuses open ZIP)
source = open_iterable('archive.zip', iterableargs={'tagname': 'item'})
all_files = source.list_tables()  # Reuses open ZIP handle
print(f"All XML files: {all_files}")

# Note: ZIPXML processes all XML files sequentially
# To process specific files, extract them and use XMLIterable directly
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `tagname` | str | None | **Yes** | XML tag name to extract records from. All elements matching this tag will be converted to records. |
| `prefix_strip` | bool | `True` | No | Strip XML namespace prefixes from element and attribute names. Set to `False` to preserve namespace prefixes. |

## ZIPXML Structure

A ZIP archive containing XML files:

```
archive.zip
├── data1.xml
│   └── <root><item>...</item></root>
├── data2.xml
│   └── <root><item>...</item></root>
└── records.xml
    └── <root><item>...</item></root>
```

The ZIPXML implementation:
1. Opens the ZIP archive
2. Iterates through XML files (`.xml` extension)
3. Extracts records matching the specified tag name
4. Yields records from all XML files sequentially

## Error Handling

```python
from iterable.helpers.detect import open_iterable

try:
    # Reading with error handling
    with open_iterable('archive.zip', iterableargs={
        'tagname': 'item'
    }) as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("ZIP file not found")
except ValueError as e:
    if "tagname" in str(e).lower():
        print("tagname parameter is required for ZIPXML files")
    else:
        print(f"Value error: {e}")
except Exception as e:
    print(f"Error reading ZIPXML: {e}")
```

### Common Errors

- **"tagname parameter is required"**: Must provide `tagname` parameter when reading ZIPXML files
- **ZIP parsing errors**: May indicate corrupted ZIP file or invalid archive format
- **XML parsing errors**: May indicate malformed XML within the archive
- **Missing lxml**: Install `lxml` package: `pip install lxml`
- **Empty archive**: ZIP files with no XML files will return empty results

## Limitations

1. **Read-only**: ZIPXML format does not support writing
2. **Tag name required**: Must specify the tag name to extract
3. **Sequential processing**: XML files are processed sequentially, not individually selectable
4. **Memory usage**: Entire XML files are parsed, which may use significant memory for large files
5. **XML files only**: Only processes files with `.xml` extension within the ZIP
6. **lxml dependency**: Requires `lxml` package

## Compression Support

ZIPXML files are already ZIP archives, so additional compression may not provide much benefit. However, they can still be compressed:
- GZip (`.zip.gz`)
- BZip2 (`.zip.bz2`)
- LZMA (`.zip.xz`)
- LZ4 (`.zip.lz4`)
- ZIP (`.zip.zip`)
- Brotli (`.zip.br`)
- ZStandard (`.zip.zst`)

## Performance Considerations

### Performance Tips

- **Tag selection**: Only elements matching the specified tag are processed, improving performance
- **Memory usage**: Large XML files within ZIP archives may use significant memory - monitor memory usage
- **File count**: Archives with many XML files will take longer to process
- **Compression**: ZIP archives are already compressed, so additional compression may not help

## Use Cases

- **Data exports**: Processing bulk XML data exports
- **Document archives**: Working with archives of XML documents
- **Bulk processing**: Processing multiple XML files efficiently
- **Legacy data**: Working with older XML-based archive formats

## Installation

ZIPXML format requires the `lxml` package:

```bash
pip install lxml
```

## Related Formats

- [XML](xml.md) - Base XML format for individual files
- ZIP compression codec (`.zip` suffix on other formats) — see [supported formats](/formats/)
- [Parquet](parquet.md) - Columnar format for bulk data
