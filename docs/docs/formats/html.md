# HTML Format

## Description

HTML (HyperText Markup Language) is the standard markup language for web pages. HTML files can contain multiple `<table>` elements, each representing tabular data. The HTML implementation in Iterable Data extracts table data from HTML files, converting each row to a dictionary record.

## File Extensions

- `.html` - Standard HTML files
- `.htm` - HTML files (alternative extension)

## Implementation Details

### Reading

The HTML implementation:
- Uses `beautifulsoup4` library for parsing
- Extracts data from `<table>` elements
- Supports multiple tables per file
- Extracts headers from `<th>` elements or generates column names
- Converts each row to a dictionary
- Handles tables with or without explicit headers

### Writing

Writing is not currently supported for HTML format.

### Key Features

- **Multiple tables**: Can read from specific table by index
- **Header detection**: Automatically extracts headers from `<th>` elements
- **Table identification**: Tables can be identified by ID, caption, or index
- **Totals support**: Can count total rows
- **Table listing**: Can discover all tables in an HTML file

## Usage

```python
from iterable import open_iterable

# Recommended: Using context manager (automatic cleanup)
# Basic reading - first table
with open_iterable('data.html') as source:
    for row in source:
        print(row)
# File automatically closed

# Read specific table by index
with open_iterable('data.html', iterableargs={
    'table_index': 1  # Second table (0-indexed)
}) as source:
    for row in source:
        print(row)

# Discover available tables
from iterable.datatypes.html import HTMLIterable

# Before opening - discover tables
iterable = HTMLIterable('data.html')
tables = iterable.list_tables('data.html')
print(f"Available tables: {tables}")

# After opening - list all tables (reuses parsed HTML)
with open_iterable("data.html", iterableargs={"table_index": 0}) as source:
    all_tables = source.list_tables()
    print(f"All tables: {all_tables}")

# Process different tables
for table_id in all_tables:
    try:
        table_index = int(table_id)
    except ValueError:
        continue
    with open_iterable("data.html", iterableargs={"table_index": table_index}) as source:
        print(f"Processing table: {table_id}")
        for row in source:
            process(row)

# Alternative: Manual close (still supported)
source = open_iterable('data.html')
try:
    for row in source:
        print(row)
finally:
    source.close()
```

### Discovering Available Tables

HTML files can contain multiple `<table>` elements. Use `list_tables()` to discover available tables:

```python
from iterable.datatypes.html import HTMLIterable

# Before opening - discover tables
iterable = HTMLIterable('data.html')
tables = iterable.list_tables('data.html')
print(f"Available tables: {tables}")
# Output: ['0', '1', 'table1', 'Summary Table']
# Tables are identified by: ID (if available), caption (if available), or index

# After opening - list all tables (reuses parsed HTML)
source = open_iterable('data.html', iterableargs={'table_index': 0})
all_tables = source.list_tables()  # Reuses parsed HTML
print(f"All tables: {all_tables}")

# Process different tables
for table_id in all_tables:
    # Tables with IDs or captions are returned as strings
    # Numeric strings represent indices
    try:
        table_index = int(table_id)
        with open_iterable('data.html', iterableargs={'table_index': table_index}) as source:
            print(f"Processing table {table_index}")
            for row in source:
                process(row)
    except ValueError:
        # Table has ID or caption - process accordingly
        print(f"Processing table: {table_id}")
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `table_index` | int | `None` | No | Index of the table to read (0-indexed). If `None`, reads the first table. |
| `encoding` | str | `utf8` | No | File encoding for reading HTML content. |

## HTML Table Structure

The HTML parser extracts data from `<table>` elements:

```html
<table id="summary">
    <caption>Sales Summary</caption>
    <tr>
        <th>Product</th>
        <th>Sales</th>
    </tr>
    <tr>
        <td>Widget A</td>
        <td>100</td>
    </tr>
</table>
```

Becomes:
```python
{
    'Product': 'Widget A',
    'Sales': '100'
}
```

Tables are identified in `list_tables()` by:
1. **ID attribute**: `<table id="summary">` → `"summary"`
2. **Caption element**: `<caption>Sales Summary</caption>` → `"Sales Summary"`
3. **Index**: If no ID or caption, uses numeric index → `"0"`, `"1"`, etc.

## Error Handling

```python
from iterable import open_iterable

try:
    # Reading with error handling
    with open_iterable('data.html', iterableargs={
        'table_index': 0
    }) as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("HTML file not found")
except ImportError as e:
    print(f"Missing dependency: {e}")
    # Install with: pip install iterabledata[html] or pip install beautifulsoup4
except Exception as e:
    print(f"Error reading HTML: {e}")
```

### Common Errors

- **"HTML format requires 'beautifulsoup4' package"**: Install BeautifulSoup4: `pip install iterabledata[html]` or `pip install beautifulsoup4`
- **Empty tables**: HTML files with no `<table>` elements will return empty results
- **Encoding errors**: If HTML file has non-UTF-8 encoding, specify `encoding` parameter

## Limitations

1. **Read-only**: HTML format does not support writing
2. **beautifulsoup4 dependency**: Requires `beautifulsoup4` package
3. **Table selection**: Must specify `table_index` to read specific tables (defaults to first table)
4. **Flat data only**: Only supports tabular data from `<table>` elements
5. **⚠️ Memory usage**: **Entire HTML file is loaded into memory** before processing. For large files (>100MB), consider:
   - Extracting tables to CSV/JSONL first using a streaming tool
   - Using XML format with `tagname="table"` if HTML structure allows
   - Processing HTML files in smaller chunks if possible
6. **Complex HTML**: Very complex HTML structures may not parse correctly

## Compression Support

HTML files can be compressed with all supported codecs:
- GZip (`.html.gz`)
- BZip2 (`.html.bz2`)
- LZMA (`.html.xz`)
- LZ4 (`.html.lz4`)
- ZIP (`.html.zip`)
- Brotli (`.html.br`)
- ZStandard (`.html.zst`)

## Performance Considerations

### Performance Tips

- **Table selection**: Specify `table_index` to read only the table you need
- **Memory usage**: Large HTML files are parsed entirely into memory - monitor memory usage for files > 100MB
- **Compression**: Compressed HTML files (`.html.gz`, `.html.zst`) can be processed efficiently

## Use Cases

- **Web scraping**: Extracting table data from HTML pages
- **Data extraction**: Converting HTML tables to structured data
- **Report processing**: Processing HTML reports with tabular data
- **Legacy data**: Working with older HTML-based data formats

## Installation

HTML format requires the `beautifulsoup4` package:

```bash
pip install iterabledata[html]
# or
pip install beautifulsoup4
```

## Related Formats

- [XML](xml.md) - Similar markup language, supports tag-based extraction
- [MHTML](mhtml.md) - MIME HTML format for web archives
- [CSV](csv.md) - Simple tabular format
