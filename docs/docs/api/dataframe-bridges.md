---
sidebar_position: 6
title: DataFrame Bridges
description: Convert iterable data to Pandas, Polars, and Dask DataFrames
---

# DataFrame Bridges

IterableData provides convenient methods to convert iterable data into popular DataFrame libraries: Pandas, Polars, and Dask. These bridges enable seamless integration with existing DataFrame-based workflows.

## Installation

DataFrame bridges require optional dependencies. Install them with:

```bash
# Install all DataFrame libraries
pip install iterabledata[dataframes]

# Or install individually
pip install pandas
pip install polars
pip install "dask[dataframe]"
```

## Pandas Bridge

### `to_pandas(chunksize=None)`

Convert iterable data to a pandas DataFrame.

**Parameters:**
- `chunksize` (int, optional): If `None`, returns a single DataFrame with all data. If specified, returns an iterator of DataFrames with at most `chunksize` rows each.

**Returns:**
- If `chunksize=None`: pandas DataFrame
- If `chunksize` specified: Iterator of pandas DataFrames

**Raises:**
- `ImportError`: If pandas is not installed

### Examples

#### Single DataFrame

```python
from iterable import open_iterable

with open_iterable('data.csv.gz') as source:
    df = source.to_pandas()
    
print(df.head())
print(f"Shape: {df.shape}")
```

#### Chunked Processing

For large files, process data in chunks to avoid memory issues:

```python
from iterable import open_iterable

with open_iterable('large_data.csv') as source:
    for df_chunk in source.to_pandas(chunksize=100_000):
        # Process each chunk
        result = df_chunk.groupby('category').sum()
        # Save or process result
        process_chunk(result)
```

#### Nested Data

Nested data structures are preserved as dict/list columns:

```python
with open_iterable('nested_data.jsonl') as source:
    df = source.to_pandas()
    
# Access nested data
print(df['nested_field'].iloc[0])  # Returns dict or list
```

## Polars Bridge

### `to_polars(chunksize=None)`

Convert iterable data to a Polars DataFrame.

**Parameters:**
- `chunksize` (int, optional): If `None`, returns a single DataFrame with all data. If specified, returns an iterator of DataFrames with at most `chunksize` rows each.

**Returns:**
- If `chunksize=None`: polars DataFrame
- If `chunksize` specified: Iterator of polars DataFrames

**Raises:**
- `ImportError`: If polars is not installed

### Examples

#### Single DataFrame

```python
from iterable import open_iterable

with open_iterable('data.csv.gz') as source:
    df = source.to_polars()
    
print(df.head())
print(f"Shape: {df.shape}")
```

#### Chunked Processing

```python
with open_iterable('large_data.csv') as source:
    for df_chunk in source.to_polars(chunksize=100_000):
        # Process each chunk with Polars
        result = df_chunk.group_by('category').agg(pl.sum('value'))
        process_chunk(result)
```

## Dask Bridge

### `to_dask(chunksize=1000000)`

Convert iterable data to a Dask DataFrame for distributed/out-of-core processing.

**Parameters:**
- `chunksize` (int, optional): Number of rows per partition. Default: 1,000,000.

**Returns:**
- Dask DataFrame

**Raises:**
- `ImportError`: If dask or pandas is not installed

### Examples

#### Single File

```python
from iterable import open_iterable

with open_iterable('data.csv.gz') as source:
    ddf = source.to_dask()
    
# Perform operations (lazy evaluation)
result = ddf.groupby('category').sum()

# Compute result
computed = result.compute()
print(computed)
```

### Multi-File Support

The `to_dask()` helper function can combine multiple files into a single Dask DataFrame, automatically detecting each file's format:

```python
from iterable.helpers.bridges import to_dask

# Combine multiple files with different formats
ddf = to_dask([
    'file1.csv',
    'file2.jsonl',
    'file3.parquet'
])

# All files are automatically detected and combined
result = ddf.groupby('category').sum().compute()
```

#### Custom Chunk Size

```python
from iterable.helpers.bridges import to_dask

# Specify chunk size for partitions
ddf = to_dask(['file1.csv', 'file2.csv'], chunksize=500_000)
```

## Performance Considerations

### Memory Usage

- **Single DataFrame**: `to_pandas()` and `to_polars()` without `chunksize` load all data into memory. Use chunked processing for large files.
- **Chunked Processing**: Use `chunksize` parameter to process data in manageable chunks.
- **Dask**: Dask DataFrames are lazy and only compute when needed, making them suitable for very large datasets.

### When to Use Each Bridge

- **Pandas**: Best for in-memory analysis, familiar API, extensive ecosystem
- **Polars**: Best for performance, modern API, efficient memory usage
- **Dask**: Best for out-of-core processing, distributed computing, very large datasets

## Error Handling

All bridge methods raise `ImportError` with helpful messages if the required library is not installed:

```python
try:
    df = source.to_pandas()
except ImportError as e:
    print(f"Install pandas: {e}")
```

## Format Support

DataFrame bridges work with all formats supported by IterableData:
- CSV, TSV, PSV, SSV
- JSON, JSONL, NDJSON
- Parquet, Arrow, Feather
- Excel (XLS, XLSX)
- And 70+ other formats

## See Also

- [BaseIterable Methods](./base-iterable.md) - Other methods available on iterable objects
- [open_iterable()](./open-iterable.md) - Main entry point for opening files
- [Engines](./engines.md) - Processing engines (DuckDB, internal)
