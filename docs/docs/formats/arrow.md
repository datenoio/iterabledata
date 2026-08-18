# Apache Arrow/Feather Format

## Description

Apache Arrow is a columnar in-memory data format designed for efficient data transfer and analytics. Feather is a file format built on Arrow that provides fast, language-agnostic columnar storage. It's optimized for speed and is ideal for data exchange between Python, R, and other languages.

## File Extensions

- `.arrow` - Apache Arrow files
- `.feather` - Feather format files (alias for Arrow)

## Implementation Details

### Reading

The Arrow/Feather implementation:
- Uses PyArrow library for reading
- Loads entire table into memory
- Supports batch reading for efficient iteration
- Preserves data types and schema

### Writing

Writing support:
- Buffers records before writing
- Uses PyArrow Feather writer
- Flushes data on close
- Maintains schema from data

### Key Features

- **Columnar format**: Efficient for analytical workloads
- **Fast I/O**: Optimized for speed
- **Type preservation**: Maintains data types
- **Cross-language**: Compatible with R, Java, and other languages
- **Totals support**: Can count total rows
- **Batch processing**: Efficient batch reading

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('data.arrow')
for row in source:
    print(row)
source.close()

# Writing
dest = open_iterable('output.feather', mode='w', iterableargs={
    'batch_size': 10000
})
dest.write({'id': 1, 'name': 'John'})
dest.close()  # Important: closes and flushes data
```

## Parameters

- `batch_size` (int): Batch size for reading (default: `1024`)

## Limitations

1. **PyArrow dependency**: Requires `pyarrow` package
2. **Memory usage**: Entire file is loaded into memory when reading
3. **Flat data only**: Designed for tabular/flat data structures
4. **Write buffering**: Must call `close()` to flush buffered data
5. **File path requirement**: Feather writing may require file path rather than stream

## Compression Support

Arrow/Feather files can be compressed with all supported codecs:
- GZip (`.arrow.gz`)
- BZip2 (`.arrow.bz2`)
- LZMA (`.arrow.xz`)
- LZ4 (`.arrow.lz4`)
- ZIP (`.arrow.zip`)
- Brotli (`.arrow.br`)
- ZStandard (`.arrow.zst`)

## Performance Considerations

- **Fast I/O**: Feather format is optimized for speed
- **Memory**: Entire file loaded into memory for reading
- **Batch size**: Larger batches improve iteration performance

## Use Cases

- **Data exchange**: Fast transfer between Python and R
- **Temporary storage**: Intermediate format in data pipelines
- **Analytics**: Fast columnar data access

## Related Formats

- [Parquet](parquet.md) - Similar columnar format with compression
- [ORC](orc.md) - Another columnar format
