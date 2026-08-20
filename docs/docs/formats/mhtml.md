# MHTML Format (MIME HTML)

## Description

MHTML (MIME HTML) is a format for archiving web pages. It combines HTML content with embedded resources (images, CSS, JavaScript) into a single file using MIME multipart encoding. MHTML files are used by Internet Explorer and other browsers for saving complete web pages.

## File Extensions

- `.mhtml` - MHTML archive files
- `.mht` - MHTML archive files (alias)

## Implementation Details

### Reading

The MHTML implementation:
- Uses Python's built-in `email` module
- Parses MIME multipart format
- Extracts HTML content and embedded resources
- Converts each part to a dictionary
- Handles content types and locations
- Extracts main HTML content

### Writing

Writing is not currently supported for MHTML format.

### Key Features

- **Web archive format**: Designed for archiving web pages
- **Multipart MIME**: Uses MIME multipart encoding
- **Resource embedding**: Embeds images, CSS, JavaScript
- **Nested data**: Supports complex web content structures
- **Content extraction**: Extracts HTML and resources

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('page.mhtml') as source:
    for part in source:
        print(part)  # Contains content type, location, and content
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **Read-only**: MHTML format does not support writing
2. **Web archive focus**: Designed for web page archiving
3. **Complex structure**: Multipart MIME structure can be complex
4. **Memory usage**: Large web pages may use significant memory

## Compression Support

MHTML files can be compressed with all supported codecs:
- GZip (`.mhtml.gz`)
- BZip2 (`.mhtml.bz2`)
- LZMA (`.mhtml.xz`)
- LZ4 (`.mhtml.lz4`)
- ZIP (`.mhtml.zip`)
- Brotli (`.mhtml.br`)
- ZStandard (`.mhtml.zst`)

## Use Cases

- **Web archiving**: Archiving complete web pages
- **Web scraping**: Saving web page content
- **Offline browsing**: Storing web pages for offline viewing
- **Content preservation**: Preserving web content

## Related Formats

- [WARC](warc.md) - Web archive format
- [EML](eml.md) - Email format (similar MIME structure)
- [MBOX](mbox.md) - Mailbox format
