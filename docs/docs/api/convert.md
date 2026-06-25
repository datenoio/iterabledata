---
sidebar_position: 2
title: convert()
description: Convert data between different file formats
---

# convert()

The `convert()` function converts data between different file formats with automatic format detection, schema extraction, and efficient batch processing.

## Signature

```python
convert(
    fromfile: str,
    tofile: str,
    iterableargs: dict = {},
    scan_limit: int = 1000,
    batch_size: int = 50000,
    silent: bool = True,
    is_flatten: bool = False,
    use_totals: bool = False,
    progress: Callable[[dict], None] | None = None,
    show_progress: bool = False,
    atomic: bool = False
) -> ConversionResult
```

## Parameters

### `fromfile` (str, required)

Path to the source file or database connection string. Format and compression are automatically detected from the filename. For database sources, use a connection string and specify the database engine in `iterableargs`.

### `tofile` (str, required)

Path to the destination file. Format and compression are automatically detected from the filename.

### `iterableargs` (dict, optional)

Format-specific arguments for reading the source file. Common options:
- `delimiter` - Field delimiter for CSV files
- `encoding` - File encoding for text files
- `tagname` - XML tag name
- `page` - Excel sheet/page

**Database source options** (when `fromfile` is a database connection string):
- `engine` - Database engine name (e.g., `'postgres'`, `'clickhouse'`, `'mysql'`, `'mongo'`)
- `query` - SQL query string or table name (required for SQL databases)
- `schema` - Schema name for table references (PostgreSQL)
- `database` - Database name (ClickHouse)
- `columns` - List of column names for projection
- `filter` - WHERE clause fragment for filtering
- `batch_size` - Number of rows per batch (default: 10000)
- `settings` - Query settings dictionary (ClickHouse)

See [Database Engines](/api/database-engines) for detailed database-specific parameters.

### `scan_limit` (int, optional)

Number of records to scan for schema detection when converting to flat formats (CSV, Parquet, etc.). Default: `1000`.

### `batch_size` (int, optional)

Number of records to process in each batch. Larger batches improve performance but use more memory. Default: `50000`.

### `silent` (bool, optional)

If `False`, shows progress bars during conversion. Default: `True`.

### `is_flatten` (bool, optional)

If `True`, flattens nested structures when converting to flat formats. Nested dictionaries become dot-notation keys (e.g., `user.name`). Default: `False`.

### `use_totals` (bool, optional)

If `True`, uses total count for progress tracking (if available). Default: `False`.

### `progress` (Callable, optional)

Optional callback function that receives progress updates during conversion. The callback receives a dictionary with:
- `rows_read`: Number of rows read from source
- `rows_written`: Number of rows written to destination
- `elapsed`: Elapsed time in seconds
- `estimated_total`: Estimated total rows (if available, otherwise `None`)

The callback is invoked periodically during conversion (every 1000 rows by default).

### `show_progress` (bool, optional)

If `True`, displays a progress bar using `tqdm` (if available). Ignored if `silent=True`. Default: `False`.

### `atomic` (bool, optional)

If `True`, writes to a temporary file and atomically renames it to the destination upon successful completion. This ensures output files are never left in a partially written state, which is important for production environments. If the conversion fails or is interrupted, the original destination file (if it existed) remains unchanged and the temporary file is cleaned up.

**Note**: Atomic writes only work on the same filesystem. If source and destination are on different filesystems, use `atomic=False` or handle the error appropriately. Default: `False`.

## Return Value

Returns a `ConversionResult` object containing conversion metrics:

- `rows_in`: Total number of rows read from source
- `rows_out`: Total number of rows written to destination
- `elapsed_seconds`: Total elapsed time in seconds
- `bytes_read`: Number of bytes read (if available, otherwise `None`)
- `bytes_written`: Number of bytes written (if available, otherwise `None`)
- `errors`: List of errors encountered during conversion (empty if none)

## Examples

### Simple Conversion

```python
from iterable.convert.core import convert

# Convert JSONL to Parquet (handles compression automatically)
convert('input.jsonl.gz', 'output.parquet')
```

### Conversion with Options

```python
from iterable.convert.core import convert

# Convert CSV with custom delimiter
convert(
    'input.csv.xz',
    'output.jsonl.zst',
    iterableargs={'delimiter': ';', 'encoding': 'utf-8'},
    batch_size=10000
)
```

### Flattening Nested Structures

```python
from iterable.convert.core import convert

# Convert JSONL to CSV with flattening
convert(
    'input.jsonl',
    'output.csv',
    is_flatten=True,
    batch_size=50000
)
```

### With Progress Tracking

```python
from iterable.convert.core import convert

# Show progress during conversion
convert(
    'input.parquet',
    'output.jsonl.zst',
    silent=False,  # Show progress bars
    use_totals=True  # Use total count if available
)
```

### With Progress Callback

```python
from iterable.convert.core import convert

def progress_callback(stats):
    print(f"Progress: {stats['rows_read']} rows read, "
          f"{stats['rows_written']} rows written, "
          f"{stats['elapsed']:.2f}s elapsed")

result = convert(
    'input.csv',
    'output.parquet',
    progress=progress_callback
)

print(f"Conversion complete: {result.rows_out} rows in {result.elapsed_seconds:.2f}s")
```

### With Progress Bar

```python
from iterable.convert.core import convert

# Show progress bar (uses tqdm if available)
result = convert(
    'input.jsonl.gz',
    'output.parquet',
    show_progress=True
)
```

### Converting from Database to File

```python
from iterable.convert.core import convert

# Convert PostgreSQL table to Parquet
convert(
    fromfile='postgresql://user:password@localhost:5432/mydb',
    tofile='users.parquet',
    iterableargs={
        'engine': 'postgres',
        'query': 'users'
    }
)

# Convert database query to JSONL with filtering
convert(
    fromfile='postgresql://localhost/mydb',
    tofile='active_users.jsonl',
    iterableargs={
        'engine': 'postgres',
        'query': 'users',
        'filter': 'active = TRUE',
        'columns': ['id', 'name', 'email']
    }
)

# Convert complex SQL query to CSV
convert(
    fromfile='postgresql://localhost/mydb',
    tofile='user_stats.csv',
    iterableargs={
        'engine': 'postgres',
        'query': '''
            SELECT 
                u.id,
                u.name,
                COUNT(o.id) as order_count
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            GROUP BY u.id, u.name
            HAVING COUNT(o.id) > 5
        '''
    }
)
```

**Note**: Database write support (converting to databases) is planned for future releases. Currently, only database → file conversion is supported.

```python
# Access metrics
print(f"Converted {result.rows_in} rows to {result.rows_out} rows")
print(f"Time: {result.elapsed_seconds:.2f} seconds")
```

### With Atomic Writes (Production Safety)

```python
from iterable.convert.core import convert

# Use atomic writes for production safety
# Ensures output file is never left in partial state
result = convert(
    'input.csv',
    'output.parquet',
    atomic=True  # Write to temp file, then atomically rename
)

# If conversion fails, original output file (if it existed) is preserved
# Temporary file is automatically cleaned up
```

### Accessing Conversion Metrics

```python
from iterable.convert.core import convert

result = convert('input.csv', 'output.jsonl')

# Access metrics programmatically
if result.errors:
    print(f"Encountered {len(result.errors)} errors during conversion")
else:
    print(f"Successfully converted {result.rows_out} rows")
    print(f"Throughput: {result.rows_out / result.elapsed_seconds:.0f} rows/second")
```

### Converting from Database to File

```python
from iterable.convert.core import convert

# Convert PostgreSQL table to Parquet
convert(
    fromfile='postgresql://user:password@localhost:5432/mydb',
    tofile='users.parquet',
    iterableargs={
        'engine': 'postgres',
        'query': 'users'
    }
)

# Convert database query to JSONL with filtering
convert(
    fromfile='postgresql://localhost/mydb',
    tofile='active_users.jsonl',
    iterableargs={
        'engine': 'postgres',
        'query': 'users',
        'filter': 'active = TRUE',
        'columns': ['id', 'name', 'email']
    }
)

# Convert complex SQL query to CSV
convert(
    fromfile='postgresql://localhost/mydb',
    tofile='user_stats.csv',
    iterableargs={
        'engine': 'postgres',
        'query': '''
            SELECT 
                u.id,
                u.name,
                COUNT(o.id) as order_count
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            GROUP BY u.id, u.name
            HAVING COUNT(o.id) > 5
        '''
    }
)
```

**Note**: Database write support (converting to databases) is planned for future releases. Currently, only database → file conversion is supported.

## How It Works

1. **Format Detection**: Automatically detects input and output formats from file extensions
2. **Schema Extraction**: For flat output formats, scans the first `scan_limit` records to extract schema
3. **Batch Processing**: Processes data in batches of `batch_size` records for efficiency
4. **Compression Handling**: Automatically handles compression for both input and output files

## Supported Conversions

You can convert between any supported formats:
- Tabular formats: CSV, TSV, PSV, Excel, Parquet, ORC
- JSON formats: JSON, JSONL, GeoJSON
- Binary formats: BSON, MessagePack, Avro, Arrow
- Other formats: XML, YAML, and 80+ more

## Error Handling

```python
from iterable.convert.core import convert

try:
    # Convert with error handling
    convert('input.jsonl.gz', 'output.parquet')
except FileNotFoundError:
    print("Input file not found")
except ValueError as e:
    print(f"Conversion error: {e}")
    # Common causes: unsupported format, schema mismatch
except Exception as e:
    print(f"Unexpected error during conversion: {e}")
```

### Common Errors

- **FileNotFoundError**: Input file doesn't exist or path is incorrect
- **ValueError**: Format not supported, schema mismatch, or invalid parameters
- **MemoryError**: Batch size too large or file too large for available memory
- **PermissionError**: Insufficient permissions to read input or write output file

## Limitations

- **Flat formats**: When converting to flat formats (CSV, Parquet), nested structures must be flattened (use `is_flatten=True`)
- **Schema detection**: For flat formats, schema is extracted from the first `scan_limit` records - ensure first records are representative
- **Memory usage**: Large `batch_size` values use more memory - adjust based on available memory
- **Format compatibility**: Some format conversions may lose data (e.g., nested structures to CSV)

## Troubleshooting

### Conversion Fails or Hangs

- **Check file formats**: Verify both input and output formats are supported
- **Check file size**: Very large files may require more memory or smaller batch sizes
- **Check permissions**: Ensure read access to input file and write access to output directory
- **Monitor memory**: Use smaller `batch_size` if running out of memory

### Data Loss or Incorrect Results

- **Nested data**: Use `is_flatten=True` when converting nested formats to flat formats
- **Schema issues**: Increase `scan_limit` if first records don't represent full schema
- **Encoding issues**: Specify encoding in `iterableargs` for text files
- **Type conversion**: Some formats may not preserve all data types exactly

### Performance Issues

- **Batch size**: Adjust `batch_size` - larger is faster but uses more memory
- **Compression**: Use compressed formats for better I/O performance
- **Progress tracking**: Set `silent=False` to monitor conversion progress

## Best Practices

1. **Choose appropriate batch size**: 10,000-50,000 records works well for most cases
2. **Use flattening carefully**: Only flatten when converting to flat formats
3. **Monitor progress**: Set `silent=False` for long conversions
4. **Use compression**: Compressed formats save space and often process faster
5. **Test with small files**: Test conversion logic on small samples before processing large files
6. **Handle errors**: Always wrap conversions in try/except blocks

## Bulk Conversion

The `bulk_convert()` function converts multiple files at once using glob patterns, directory paths, or file lists. It's perfect for batch ETL operations and format migrations.

### Signature

```python
bulk_convert(
    source: str,
    dest: str,
    pattern: str | None = None,
    to_ext: str | None = None,
    iterableargs: dict = {},
    toiterableargs: dict = {},
    scan_limit: int = 1000,
    batch_size: int = 50000,
    silent: bool = True,
    is_flatten: bool = False,
    use_totals: bool = False,
    progress: Callable[[dict], None] | None = None,
    show_progress: bool = False,
    atomic: bool = False,
    parallel: bool = False,
    workers: int | None = None
) -> BulkConversionResult
```

### Parameters

#### `source` (str, required)

Glob pattern (e.g., `'data/raw/*.csv.gz'`), directory path, or single file path. The function automatically discovers all matching files.

#### `dest` (str, required)

Output directory path where converted files will be written. The directory will be created if it doesn't exist.

#### `pattern` (str, optional)

Filename pattern for output files (e.g., `'{name}.parquet'`). Supports placeholders:
- `` `{name}` `` - Full filename with extension (e.g., `data.csv.gz`)
- `` `{stem}` `` - Filename without any extensions (e.g., `data`)
- `` `{ext}` `` - All extensions as one string (e.g., `csv.gz`)

If `None`, uses `to_ext` or keeps original name.

#### `to_ext` (str, optional)

Target file extension (e.g., `'parquet'`). Used if `pattern` is `None`. Extension replacement removes all existing extensions and adds the new one. Either `pattern` or `to_ext` must be specified.

#### `atomic` (bool, optional)

If `True`, each file conversion uses atomic writes (writes to temporary file, then atomically renames). Default: `False`.

#### `parallel` (bool, optional)

If `True`, enables parallel file conversion using threading. Recommended for I/O-bound operations where multiple files can be converted concurrently. Default: `False`.

**Benefits of Parallel Conversion**:
- ✅ Faster processing for multiple files
- ✅ Better CPU utilization
- ✅ Reduced total conversion time

**When to Use Parallel**:
- Converting many files (10+ files)
- I/O-bound operations (reading from disk/network)
- Files are independent (no shared state)

**When NOT to Use Parallel**:
- Very few files (overhead may not be worth it)
- CPU-bound operations (threading doesn't help)
- Limited system resources

#### `workers` (int, optional)

Number of worker threads for parallel conversion. If `None`, uses `min(4, CPU count)`. Only used when `parallel=True`. Default: `None`.

**Choosing Worker Count**:
- **I/O-bound**: Use more workers (e.g., 8-16) to keep I/O busy
- **CPU-bound**: Use fewer workers (e.g., 2-4) to avoid context switching overhead
- **Default**: `min(4, CPU count)` works well for most cases

#### Other Parameters

All other parameters (`iterableargs`, `batch_size`, `is_flatten`, etc.) are passed through to the underlying `convert()` function for each file.

### Return Value

Returns a `BulkConversionResult` object containing aggregated metrics:
- `total_files`: Total number of files processed
- `successful_files`: Number of files successfully converted
- `failed_files`: Number of files that failed to convert
- `total_rows_in`: Total number of rows read across all files
- `total_rows_out`: Total number of rows written across all files
- `total_elapsed_seconds`: Total elapsed time in seconds
- `file_results`: List of `FileConversionResult` objects (one per file)
- `errors`: List of all errors encountered
- `throughput`: Rows per second (calculated property)

### Examples

#### Convert Files Matching Glob Pattern

```python
from iterable.convert.core import bulk_convert

# Convert all compressed CSV files to Parquet
result = bulk_convert(
    'data/raw/*.csv.gz',
    'data/processed/',
    to_ext='parquet'
)

print(f"Converted {result.successful_files}/{result.total_files} files")
print(f"Total rows: {result.total_rows_out}")
```

#### Convert with Custom Filename Pattern

```python
from iterable.convert.core import bulk_convert

# Convert CSV files with custom pattern
result = bulk_convert(
    'data/*.csv',
    'output/',
    pattern='{name}.parquet'  # data.csv -> data.csv.parquet
)

# Or use stem to remove original extension
result = bulk_convert(
    'data/*.csv.gz',
    'output/',
    pattern='{stem}.parquet'  # data.csv.gz -> data.parquet
)
```

#### Convert Entire Directory

```python
from iterable.convert.core import bulk_convert

# Convert all files in directory
result = bulk_convert(
    'data/raw/',
    'data/processed/',
    to_ext='parquet'
)
```

#### Convert with All Parameters

```python
from iterable.convert.core import bulk_convert

# Convert with custom batch size and flattening
result = bulk_convert(
    'data/*.jsonl',
    'output/',
    to_ext='parquet',
    batch_size=10000,
    is_flatten=True,
    iterableargs={'encoding': 'utf-8'}
)
```

#### Handle Results and Errors

```python
from iterable.convert.core import bulk_convert

result = bulk_convert('data/*.csv', 'output/', to_ext='jsonl')

# Check overall success
if result.failed_files > 0:
    print(f"Warning: {result.failed_files} files failed to convert")

# Access per-file results
for file_result in result.file_results:
    if file_result.success:
        print(f"✓ {file_result.source_file} -> {file_result.dest_file}")
        print(f"  Rows: {file_result.result.rows_out}")
    else:
        print(f"✗ {file_result.source_file} failed: {file_result.error}")

# Access aggregated metrics
print(f"Total throughput: {result.throughput:.0f} rows/second")
```

#### Progress Tracking

```python
from iterable.convert.core import bulk_convert

def progress_callback(stats):
    print(f"File {stats['file_index']}/{stats['total_files']}: "
          f"{stats['current_file']}")
    print(f"  Rows: {stats['file_rows_read']} read, "
          f"{stats['file_rows_written']} written")

result = bulk_convert(
    'data/*.csv',
    'output/',
    to_ext='parquet',
    progress=progress_callback
)
```

#### Parallel Conversion

```python
from iterable.convert.core import bulk_convert

# Convert multiple files in parallel for faster processing
result = bulk_convert(
    'data/raw/*.csv.gz',
    'data/processed/',
    to_ext='parquet',
    parallel=True,  # Enable parallel processing
    workers=8      # Use 8 worker threads (optional)
)

print(f"Converted {result.successful_files} files in parallel")
print(f"Total time: {result.total_elapsed_seconds:.2f}s")
```

**Parallel Conversion Notes**:
- Progress callbacks work in parallel mode (may be called out of order)
- Atomic writes are supported in parallel mode
- Errors from individual files don't stop other conversions
- Best performance when converting many files (10+)

### Error Handling

`bulk_convert()` continues processing remaining files even if one fails. Errors are collected in the result object:

```python
from iterable.convert.core import bulk_convert

result = bulk_convert('data/*.csv', 'output/', to_ext='jsonl')

# Check for errors
if result.errors:
    print(f"Encountered {len(result.errors)} errors:")
    for error in result.errors:
        print(f"  - {error}")

# Check per-file results
for file_result in result.file_results:
    if not file_result.success:
        print(f"Failed: {file_result.source_file}")
        print(f"  Error: {file_result.error}")
```

### Best Practices

1. **Use glob patterns**: Glob patterns are more flexible than directory paths
2. **Specify output format**: Always provide either `pattern` or `to_ext`
3. **Handle errors**: Check `failed_files` and `errors` in results
4. **Monitor progress**: Use `progress` callback for long-running conversions
5. **Test with small sets**: Test on a few files before processing large batches

## Related Topics

- [Format Conversion Use Case](/use-cases/format-conversion)
- [open_iterable()](/api/open-iterable) - Manual conversion
- [Supported Formats](/formats/)
