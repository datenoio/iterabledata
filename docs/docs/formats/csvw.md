# CSVW Format

## Description

CSVW (CSV on the Web) is a W3C standard for describing CSV files with metadata. It uses JSON-LD to provide metadata about CSV files, including column descriptions, data types, and other annotations. This allows CSV files to be self-describing and machine-readable.

## File Extensions

- `.csvw` - CSVW files (CSV with metadata)
- `.csv` - CSV files (when used with metadata file)

## Implementation Details

### Reading

The CSVW implementation:
- Reads CSV files with associated metadata
- Automatically locates metadata file (`.csv-metadata.json` or `-metadata.json`)
- Applies type conversions based on metadata schema
- Extracts column information from metadata
- Uses standard CSV reading with metadata enhancements

### Writing

Writing support:
- Writes CSV files
- Can write metadata annotations if provided
- Supports type-aware writing based on schema
- Maintains column order from metadata

### Key Features

- **W3C standard**: Official W3C standard for CSV metadata
- **Type conversion**: Automatic type conversion based on metadata
- **Self-describing**: CSV files become self-describing with metadata
- **Schema support**: Full support for CSVW table schema
- **Metadata discovery**: Automatically finds associated metadata files

## Usage

```python
from iterable import open_iterable

# Basic reading (automatically finds metadata file)
with open_iterable('data.csv') as source:
    for row in source:
        print(row)  # Rows are dicts with type-converted values

# Reading with explicit metadata file
with open_iterable('data.csv', iterableargs={'metadata_file': 'data.csv-metadata.json'}) as source:
    for row in source:
        print(row)

# Writing
with open_iterable('output.csvw', mode='w', iterableargs={'keys': ['id', 'name']}) as dest:
    dest.write({'id': '1', 'name': 'John'})
```

## Parameters

- `metadata_file` (str): Path to CSVW metadata JSON file (optional, auto-detected if not provided)
- `delimiter` (str): CSV delimiter (default: `,`)
- `quotechar` (str): CSV quote character (default: `"`)
- `encoding` (str): File encoding (default: `utf8`)

## Metadata File Format

The CSVW metadata file is a JSON-LD file that describes the CSV structure:

```json
{
  "@context": "http://www.w3.org/ns/csvw",
  "url": "data.csv",
  "tableSchema": {
    "columns": [
      {
        "name": "id",
        "titles": "id",
        "datatype": {"base": "string"}
      },
      {
        "name": "name",
        "titles": "name",
        "datatype": {"base": "string"}
      }
    ]
  }
}
```

## Limitations

1. **Metadata file**: Requires separate metadata JSON file
2. **Type conversion**: Type conversion is based on metadata; without metadata, behaves like regular CSV
3. **Schema complexity**: Full CSVW standard is complex; this is a simplified implementation
4. **Flat data only**: Only supports flat/tabular data

## Compression Support

CSVW files (CSV + metadata) can be compressed with all supported codecs:
- GZip (`.csvw.gz` or `.csv.gz`)
- BZip2 (`.csvw.bz2` or `.csv.bz2`)
- LZMA (`.csvw.xz` or `.csv.xz`)
- LZ4 (`.csvw.lz4` or `.csv.lz4`)
- ZIP (`.csvw.zip` or `.csv.zip`)
- Brotli (`.csvw.br` or `.csv.br`)
- ZStandard (`.csvw.zst` or `.csv.zst`)

Note: Metadata files (`.json`) are typically not compressed separately.

## Use Cases

- **Data publishing**: Publishing CSV data with rich metadata
- **Data integration**: Integrating CSV data with type information
- **Semantic web**: Making CSV data part of the semantic web
- **Data validation**: Validating CSV data against schemas
- **Type safety**: Ensuring correct data types in CSV processing

## Related Formats

- [CSV](csv.md) - Base CSV format
- [AnnotatedCSV](annotatedcsv.md) - InfluxDB annotated CSV format
- [JSON](json.md) - JSON format (for metadata)
- [JSON-LD](json.md) - JSON-LD format (metadata format)
