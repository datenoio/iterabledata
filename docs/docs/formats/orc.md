# ORC Format

## Description

ORC (Optimized Row Columnar) is a columnar storage format designed for Hadoop workloads. It provides efficient compression and fast columnar access, making it ideal for analytical queries. ORC files store data in a column-oriented format with built-in compression and indexing.

## File Extensions

- `.orc` - ORC files

## Implementation Details

### Reading

The ORC implementation:
- Uses `pyorc` library for reading
- Supports schema inference from file
- Converts ORC records to Python dictionaries
- Efficient columnar reading

### Writing

Writing support:
- Requires schema or keys specification
- Supports compression (default: level 5)
- Writes ORC files with schema
- Efficient columnar writing

### Key Features

- **Columnar storage**: Efficient for analytical queries
- **Compression**: Built-in compression support
- **Schema support**: Requires schema definition for writing
- **Totals support**: Can count total rows
- **Type preservation**: Maintains data types

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('data.orc')
for row in source:
    print(row)
source.close()

# Writing with schema
dest = open_iterable('output.orc', mode='w', iterableargs={
    'keys': ['id', 'name', 'age'],
    'compression': 5  # Compression level (0-9)
})
dest.write({'id': '1', 'name': 'John', 'age': '30'})
dest.close()
```

## Parameters

- `keys` (list[str]): Column names (required for writing if schema not provided)
- `schema` (list[str]): ORC schema definition (optional, overrides keys)
- `compression` (int): Compression level 0-9 (default: `5`)

## Limitations

1. **pyorc dependency**: Requires `pyorc` package
2. **Schema required**: Must specify schema or keys for writing
3. **Flat data only**: Designed for tabular/flat data structures
4. **Binary format**: Not human-readable
5. **Hadoop ecosystem**: Primarily designed for Hadoop environments

## Compression Support

ORC has built-in compression (separate from file-level compression):
- Compression levels 0-9
- Default compression level: 5

ORC files can also be compressed with file-level codecs:
- GZip (`.orc.gz`)
- BZip2 (`.orc.bz2`)
- LZMA (`.orc.xz`)
- LZ4 (`.orc.lz4`)
- ZIP (`.orc.zip`)
- Brotli (`.orc.br`)
- ZStandard (`.orc.zst`)

## Use Cases

- **Hadoop ecosystems**: Data storage in Hadoop
- **Data warehousing**: Analytical data storage
- **ETL pipelines**: Intermediate format for data transformation
- **Big data**: Large-scale data processing

## Related Formats

- [Parquet](parquet.md) - Similar columnar format
- [Arrow](arrow.md) - Another columnar format
- [Delta Lake](delta.md) - Transactional layer over Parquet
