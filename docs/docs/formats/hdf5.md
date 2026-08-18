# HDF5 Format

## Description

HDF5 (Hierarchical Data Format version 5) is a data model, library, and file format for storing and managing data. It's designed for storing large amounts of numerical data and is commonly used in scientific computing, particularly for arrays and tables.

## File Extensions

- `.hdf5` - HDF5 files
- `.h5` - HDF5 files (alias)

## Implementation Details

### Reading

The HDF5 implementation:
- Uses `h5py` library for reading
- Requires `dataset_path` parameter to specify which dataset to read
- Supports 1D and 2D arrays
- Handles structured arrays (tables)
- Requires file path (not stream)

### Writing

Writing support:
- Creates HDF5 files and datasets
- Writes data to specified dataset path
- Requires file path (not stream)

### Key Features

- **Hierarchical structure**: Supports groups and datasets
- **Large data**: Designed for large numerical datasets
- **Scientific computing**: Common in scientific applications
- **Totals support**: Can count total rows in dataset

## Usage

```python
from iterable import open_iterable

# List available datasets
from iterable.datatypes.hdf5 import HDF5Iterable

# Discover datasets before opening
datasets = HDF5Iterable('data.h5').list_tables('data.h5')
print(f"Available datasets: {datasets}")  # e.g., ['/data', '/group/dataset1']

# Reading with dataset path
source = open_iterable('data.h5', iterableargs={
    'dataset_path': '/data'  # Path to dataset in HDF5 file
})
for row in source:
    print(row)
source.close()

# List datasets after opening (reuses file handle)
source = open_iterable('data.h5', iterableargs={'dataset_path': '/data'})
all_datasets = source.list_tables()  # Reuses open file handle
print(f"All datasets: {all_datasets}")
source.close()

# Writing
dest = open_iterable('output.h5', mode='w', iterableargs={
    'dataset_path': '/data'
})
dest.write({'col1': 1, 'col2': 2})
dest.close()
```

## Parameters

- `dataset_path` (str): **Required** - Path to dataset in HDF5 file (e.g., `/data`, `/group/dataset`)

## Limitations

1. **h5py dependency**: Requires `h5py` package
2. **Dataset path required**: Must specify which dataset to read/write
3. **File path required**: Requires filename, not stream
4. **Flat data only**: Only supports tabular/array data
5. **Structure complexity**: Complex HDF5 structures may require manual handling

## Compression Support

HDF5 has built-in compression support (separate from file-level compression):
- HDF5 supports various compression filters (gzip, szip, etc.)

HDF5 files can also be compressed with file-level codecs:
- GZip (`.h5.gz`)
- BZip2 (`.h5.bz2`)
- LZMA (`.h5.xz`)
- LZ4 (`.h5.lz4`)
- ZIP (`.h5.zip`)
- Brotli (`.h5.br`)
- ZStandard (`.h5.zst`)

## Use Cases

- **Scientific computing**: Storing large numerical datasets
- **Machine learning**: Storing training data
- **Data analysis**: Large-scale data analysis
- **Simulations**: Storing simulation results

## Related Formats

- [Parquet](parquet.md) - Columnar format for analytics
- [Arrow](arrow.md) - Columnar in-memory format
