---
sidebar_position: 1
title: open_iterable()
description: Main entry point for opening data files
---

# open_iterable()

The `open_iterable()` function is the main entry point for reading and writing data files. It automatically detects the file format and compression codec from the filename.

## Signature

```python
open_iterable(
    filename: str,
    mode: str = 'r',
    engine: str = 'internal',
    codecargs: dict = {},
    iterableargs: dict = {}
) -> BaseIterable
```

## Parameters

### `filename` (str, required)

Path to the file to open. Supports both local file paths and cloud storage URIs. The function automatically detects:
- **Format**: From file extension (`.csv`, `.jsonl`, `.parquet`, etc.) or content analysis (magic numbers and heuristics)
- **Compression**: From file extension (`.gz`, `.bz2`, `.xz`, `.zst`, etc.)

**Supported Path Types:**
- **Local files**: Standard file paths (e.g., `data.csv`, `/path/to/file.jsonl`)
- **Cloud storage URIs**: Direct access to cloud object storage
  - Amazon S3: `s3://bucket/path/file.csv`, `s3a://bucket/path/file.csv`
  - Google Cloud Storage: `gs://bucket/path/file.csv`, `gcs://bucket/path/file.csv`
  - Azure Blob Storage: `az://container/path/file.csv`, `abfs://container/path/file.csv`, `abfss://container/path/file.csv`
  - See [Cloud Storage Support](/api/cloud-storage) for detailed documentation

**Format Detection Strategy:**
1. **Primary**: Filename extension detection (fast and reliable)
2. **Fallback**: Content-based detection when extension is missing or unknown
   - **Binary formats**: Magic number detection (e.g., `PAR1` for Parquet, `ORC` for ORC)
   - **Text formats**: Content heuristics (e.g., JSON structure, CSV delimiter patterns)
3. Works with files without extensions, streams, files with incorrect extensions, and cloud storage URIs

### `mode` (str, optional)

File mode:
- `'r'` - Read mode (default)
- `'w'` - Write mode

### `engine` (str, optional)

Processing engine:
- `'internal'` - Internal Python engine (default, supports all formats)
- `'duckdb'` - DuckDB engine (faster for CSV/JSONL, limited format support)
- `'postgres'` or `'postgresql'` - PostgreSQL database engine (read-only)
- `'clickhouse'` - ClickHouse database engine (read-only)
- Other database engines: `'mysql'`, `'mssql'`, `'sqlite'`, `'mongo'`, `'elasticsearch'` (see [Database Engines](/api/database-engines) for details)

### `codecargs` (dict, optional)

Arguments passed to the compression codec initialization. Most codecs don't require additional arguments.

### `iterableargs` (dict, optional)

Format-specific arguments. Common options:
- `delimiter` - Field delimiter for CSV/TSV files (default: `,`)
- `encoding` - File encoding for text files (default: auto-detected)
- `tagname` - XML tag name to iterate over (required for XML files)
- `page` - Sheet/page number or name for Excel files
- `keys` - Column names for files without headers
- `autodetect` - Automatically detect delimiter (CSV files)
- `storage_options` - Cloud storage authentication options (dict). See [Cloud Storage Support](/api/cloud-storage) for details

**Error Handling Options:**
- `on_error` - Error handling policy (default: `'raise'`). Options:
  - `'raise'` - Raise exception immediately when parse error occurs (default, maintains backward compatibility)
  - `'skip'` - Silently skip malformed records and continue iteration
  - `'warn'` - Log warning using Python's `warnings` module and continue iteration
- `error_log` - Error logging destination (optional). Can be:
  - File path string - Errors are logged to the specified file (created/opened in append mode)
  - File-like object - Errors are written to the provided file object
  - When provided, all errors (regardless of `on_error` policy) are logged with contextual information:
    - Timestamp (ISO format)
    - Filename
    - Row number (if available)
    - Byte offset (if available)
    - Error type and message
    - Original line content (for text formats, if available)

**DuckDB Engine-specific options** (only when `engine='duckdb'`):
- `columns` - List of column names to read (projection pushdown). Example: `['name', 'age']`
- `filter` - Filter condition as SQL string or Python callable. Example: `"age > 18"` or `lambda row: row['age'] > 18`
- `query` - Direct SQL query string. When provided, `columns` and `filter` are ignored. Example: `"SELECT name FROM read_csv_auto('file.csv') WHERE age > 18"`

**Database Engine-specific options** (when using database engines like `engine='postgres'` or `engine='clickhouse'`):
- `query` - SQL query string or table name (required). Example: `"users"` or `"SELECT * FROM users WHERE active = TRUE"`
- `schema` - Schema name for table references (PostgreSQL). Example: `"public"`
- `database` - Database name (ClickHouse). Example: `"analytics"`
- `columns` - List of column names for projection. Example: `['id', 'name', 'email']`
- `filter` - WHERE clause fragment. Example: `"active = TRUE AND age > 18"`
- `batch_size` - Number of rows per batch (default: 10000). Example: `5000`
- `read_only` - Use read-only transaction/validation (default: `True`)
- `settings` - Query settings dictionary (ClickHouse). Example: `{"max_threads": 4, "max_memory_usage": 10000000000}`
- `format` - Result format (ClickHouse). Example: `"native"` or `"JSONEachRow"`
- `server_side_cursor` - Use server-side cursor for streaming (PostgreSQL, default: `True`)
- `connect_args` - Additional connection arguments. Example: `{"sslmode": "require"}`

**Performance Options:**
- `read_ahead` - Enable read-ahead caching for improved I/O performance (default: `False`). When enabled, prefetches rows ahead of consumption to reduce I/O wait time. Particularly beneficial for network sources and slow I/O.
- `read_ahead_size` - Number of rows to prefetch when read-ahead is enabled (default: `10`). Larger values use more memory but reduce I/O wait time.
- `read_ahead_refill_threshold` - Refill buffer when it drops below this fraction (0.0-1.0, default: `0.3`). Buffer is refilled when it contains fewer than `read_ahead_size * read_ahead_refill_threshold` rows.

See [Database Engines](/api/database-engines) for detailed documentation on database-specific parameters.

## Returns

Returns a `BaseIterable` object that can be iterated over or used for writing.

## Examples

### Basic Reading

```python
from iterable.helpers.detect import open_iterable

# Automatically detects format and compression
with open_iterable('data.csv.gz') as source:
    for row in source:
        print(row)
```

### Writing Data

```python
from iterable.helpers.detect import open_iterable

with open_iterable('output.jsonl.zst', mode='w') as dest:
    dest.write({'name': 'John', 'age': 30})
```

### With Format-Specific Options

```python
from iterable.helpers.detect import open_iterable

# CSV with custom delimiter
with open_iterable('data.csv', iterableargs={
    'delimiter': ';',
    'encoding': 'utf-8'
}) as source:
    for row in source:
        print(row)

# XML with tag name
with open_iterable('data.xml', iterableargs={
    'tagname': 'item'
}) as source:
    for row in source:
        print(row)

# Excel with specific sheet
with open_iterable('data.xlsx', iterableargs={
    'page': 'Sheet2'
}) as source:
    for row in source:
        print(row)
```

### Using DuckDB Engine

```python
from iterable.helpers.detect import open_iterable

# Use DuckDB for fast queries
with open_iterable('data.csv.gz', engine='duckdb') as source:
    total = source.totals()
    for row in source:
        print(row)
```

### Using Database Engines

```python
from iterable.helpers.detect import open_iterable

# Read from PostgreSQL database
with open_iterable(
    'postgresql://user:password@localhost:5432/mydb',
    engine='postgres',
    iterableargs={'query': 'users'}
) as source:
    for row in source:
        print(row)

# Read from ClickHouse database
with open_iterable(
    'clickhouse://user:password@localhost:9000/analytics',
    engine='clickhouse',
    iterableargs={'query': 'events', 'settings': {'max_threads': 4}}
) as source:
    for row in source:
        print(row)

# Read specific columns with filtering
with open_iterable(
    'postgresql://localhost/mydb',
    engine='postgres',
    iterableargs={
        'query': 'users',
        'columns': ['id', 'name', 'email'],
        'filter': 'active = TRUE'
    }
) as source:
    for row in source:
        print(row)

# Use custom SQL query
with open_iterable(
    'postgresql://localhost/mydb',
    engine='postgres',
    iterableargs={
        'query': 'SELECT id, name FROM users WHERE age > 18 ORDER BY name LIMIT 100'
    }
) as source:
    for row in source:
        print(row)
```

See [Database Engines](/api/database-engines) for comprehensive database engine documentation.

## Supported Formats

The function supports 140+ formats. See [Supported Formats](/formats/) for a complete list.

## Supported Compression Codecs

- GZip (`.gz`)
- BZip2 (`.bz2`)
- LZMA (`.xz`, `.lzma`)
- LZ4 (`.lz4`)
- ZIP (`.zip`)
- Brotli (`.br`)
- ZStandard (`.zst`, `.zstd`)
- Snappy (`.snappy`, `.sz`)
- LZO (`.lzo`, `.lzop`)

## Error Handling

```python
from iterable.helpers.detect import open_iterable

# Recommended: Using context manager with error handling
try:
    with open_iterable('data.csv') as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("File not found")
except UnicodeDecodeError:
    print("Encoding error - try specifying encoding explicitly")
    # Retry with explicit encoding
    with open_iterable('data.csv', iterableargs={'encoding': 'latin-1'}) as source:
        for row in source:
            process(row)
except ValueError as e:
    print(f"Format error: {e}")
    # Common causes: missing required parameters, unsupported format
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Common Exceptions

The library uses a comprehensive exception hierarchy for better error handling:

**Base Exception:**
- **IterableDataError**: Base exception for all library errors

**Format Exceptions:**
- **FormatError**: Base exception for format-related errors
- **FormatNotSupportedError**: Format is not supported or dependencies are missing
- **FormatDetectionError**: Could not detect file format from filename or content
- **FormatParseError**: Format parsing failed (malformed data)

**Codec Exceptions:**
- **CodecError**: Base exception for compression codec errors
- **CodecNotSupportedError**: Compression codec is not supported
- **CodecDecompressionError**: Decompression failed
- **CodecCompressionError**: Compression failed

**Read/Write Exceptions:**
- **ReadError**: Error during data reading operations
- **WriteError**: Error during data writing operations
- **StreamingNotSupportedError**: Format doesn't support streaming

**Resource Exceptions:**
- **ResourceError**: Base exception for resource management errors
- **StreamNotSeekableError**: Stream doesn't support seeking (required for `reset()`)
- **ResourceLeakError**: Resource leak detected

**Standard Exceptions:**
- **FileNotFoundError**: File doesn't exist or path is incorrect
- **UnicodeDecodeError**: Encoding issue - specify encoding explicitly
- **ImportError**: Missing optional dependency (e.g., `duckdb`, `pyarrow`)
- **PermissionError**: Insufficient file permissions

**Example Error Handling:**
```python
from iterable.helpers.detect import open_iterable
from iterable.exceptions import (
    FormatDetectionError,
    FormatNotSupportedError,
    CodecError
)

try:
    with open_iterable('data.unknown') as source:
        for row in source:
            process(row)
except FormatDetectionError as e:
    print(f"Could not detect format: {e.reason}")
    # Try with explicit format or check file content
except FormatNotSupportedError as e:
    print(f"Format '{e.format_id}' not supported: {e.reason}")
    # Install missing dependencies or use different format
except CodecError as e:
    print(f"Compression error with {e.codec_name}: {e}")
    # Check file integrity or try different codec
except FileNotFoundError:
    print("File not found")
```

## Troubleshooting

### File Not Opening

- **Check file path**: Verify file exists and path is correct
- **Check format**: Ensure file extension matches format
- **Check permissions**: Verify read/write permissions
- **Check dependencies**: Some formats require optional packages

### Wrong Format Detected

- **Check extension**: File extension is the primary method for format detection
- **Content-based detection**: The library automatically uses content analysis (magic numbers/heuristics) when extension detection fails
- **Files without extensions**: Content-based detection works for files without extensions or with incorrect extensions
- **Use `detect_file_type()`**: Verify format detection before opening
- **Specify format explicitly**: Some formats may need explicit parameters

## Format Detection Details

IterableData uses a two-stage format detection strategy to automatically identify file formats:

### Stage 1: Filename Extension Detection

The primary detection method uses the file extension (e.g., `.csv`, `.jsonl`, `.parquet`). This is fast, reliable, and works for the vast majority of files.

**Examples:**
- `data.csv` → CSV format
- `data.jsonl.gz` → JSONL format with GZIP compression
- `data.parquet` → Parquet format

### Stage 2: Content-Based Detection (Fallback)

When filename detection fails (no extension, unknown extension, or incorrect extension), the library automatically falls back to content-based detection. This analyzes the file's content using:

#### Binary Format Detection (Magic Numbers)

Binary formats are identified by their unique "magic numbers" - specific byte sequences at the beginning of files:

| Format | Magic Number | Detection |
|--------|--------------|-----------|
| Parquet | `PAR1` | First 4 bytes |
| ORC | `ORC` | First 3 bytes |
| Vortex | `VTXF` | First 4 bytes |
| Paimon Row | `ROWS` | Last 4 bytes of 32-byte footer |
| Paimon Mosaic | `MOSA` | Last 4 bytes of 32-byte footer |
| PCAP | `\xa1\xb2\xc3\xd4` or `\xd4\xc3\xb2\xa1` | First 4 bytes (big/little-endian) |
| PCAPNG | `\x0a\x0d\x0d\x0a` | First 4 bytes |
| Arrow/Feather | `ARROW1` | First 6 bytes |
| XLSX | `PK\x03\x04` + `xl/` | ZIP header + directory indicator |
| ZIP | `PK\x03\x04` | First 4 bytes |

**Example:**
```python
from iterable.helpers.detect import open_iterable

# File without extension but with Parquet magic number
with open_iterable('data') as source:  # Contains PAR1 magic number
    for row in source:
        print(row)  # Automatically detected as Parquet
```

#### Text Format Detection (Heuristics)

Text formats are identified using content heuristics that analyze the structure and patterns:

**JSON Detection:**
- Checks if content starts with `{` or `[`
- Validates JSON syntax by attempting to parse
- Detects JSONL (newline-delimited JSON) by checking if each line is valid JSON

**CSV/TSV/PSV Detection:**
- Analyzes delimiter patterns (comma, tab, pipe)
- Checks for consistent delimiter usage across multiple lines
- Requires at least 2 lines with consistent delimiter counts

**Example:**
```python
from iterable.helpers.detect import open_iterable

# File without extension but with JSON content
with open_iterable('data') as source:  # Contains {"name": "test"}
    for row in source:
        print(row)  # Automatically detected as JSON
```

### Detection Behavior

1. **Filename takes priority**: If a file has a recognized extension, filename detection is used (even if content suggests a different format)
2. **Content detection is fallback**: Content-based detection only runs when filename detection fails
3. **File position preserved**: Content detection reads a small sample (8KB by default) and restores the file position, so it doesn't interfere with reading
4. **Cloud storage support**: Content-based detection works with cloud storage URIs (S3, GCS, Azure) when the stream is seekable

### When Content Detection is Used

Content-based detection is automatically used in these scenarios:

- **Files without extensions**: `data` (no extension)
- **Unknown extensions**: `data.unknown` (extension not recognized)
- **Incorrect extensions**: `data.csv` containing JSON content (though filename takes priority)
- **Streams**: When opening from file-like objects without filenames
- **Cloud storage**: When cloud URIs don't have recognized extensions

### Limitations

- **Binary vs Text ambiguity**: Some binary formats may be misidentified if they contain text-like content
- **Heuristic accuracy**: Text format heuristics are best-effort and may not be 100% accurate for edge cases
- **Performance**: Content detection reads a sample of the file, adding a small overhead (typically under 1ms)
- **Seekable streams required**: Content detection requires seekable streams (some network streams may not support this)

### Manual Format Specification

If automatic detection fails or you want to override it, you can specify the format explicitly:

```python
from iterable.helpers.detect import open_iterable

# Specify format explicitly (bypasses detection)
with open_iterable('data', iterableargs={'format': 'json'}) as source:
    for row in source:
        print(row)
```

### Verifying Detection

You can verify format detection before opening:

```python
from iterable.helpers.detect import detect_file_type

# Detect format without opening
result = detect_file_type('data.csv')
print(f"Format: {result['datatype']}")
print(f"Compression: {result['codec']}")
print(f"Success: {result['success']}")
print(f"Confidence: {result['confidence']:.2f}")
print(f"Method: {result['detection_method']}")

# With content-based detection
with open('data', 'rb') as f:
    result = detect_file_type('data', fileobj=f)
    print(f"Detected format: {result['datatype']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Method: {result['detection_method']}")
```

### Confidence Scores

Detection results include confidence scores (0.0-1.0) that indicate how certain the detection is:

**Confidence Levels:**
- **1.0 (Highest)**: Filename-based detection - Very reliable, file extension matches format
- **0.95-0.99 (Very High)**: Magic number detection - Binary formats identified by unique headers
- **0.85-0.90 (High)**: Strong heuristic matches - Valid JSON/JSONL with multiple confirmations
- **0.75-0.85 (Medium-High)**: Heuristic detection - CSV/TSV with consistent delimiter patterns
- **0.70-0.75 (Medium)**: Weak heuristic matches - Partial matches or ambiguous content

**Detection Methods:**
- **`filename`**: Detection based on file extension (highest confidence)
- **`magic_number`**: Detection based on binary format magic numbers (very high confidence)
- **`heuristic`**: Detection based on content analysis and pattern matching (variable confidence)

**Example:**
```python
from iterable.helpers.detect import detect_file_type

# Filename detection - highest confidence
result = detect_file_type('data.csv')
print(f"Confidence: {result['confidence']}")  # 1.0
print(f"Method: {result['detection_method']}")  # "filename"

# Content-based detection - variable confidence
with open('data', 'rb') as f:
    result = detect_file_type('data', fileobj=f)
    if result['detection_method'] == 'magic_number':
        print(f"High confidence: {result['confidence']}")  # 0.95-0.99
    elif result['detection_method'] == 'heuristic':
        print(f"Medium confidence: {result['confidence']}")  # 0.70-0.90
```

**Using Confidence Scores:**
```python
from iterable.helpers.detect import detect_file_type

result = detect_file_type('data.unknown', fileobj=open('data.unknown', 'rb'))

if result['success']:
    if result['confidence'] >= 0.95:
        # Very confident - proceed with detection
        print(f"High confidence detection: {result['datatype']}")
    elif result['confidence'] >= 0.80:
        # Good confidence - likely correct
        print(f"Good confidence detection: {result['datatype']}")
    else:
        # Lower confidence - may want to verify or specify format explicitly
        print(f"Lower confidence ({result['confidence']:.2f}) - consider verifying")
        print(f"Detected as: {result['datatype']}")
```

### Read-Ahead Caching

Read-ahead caching prefetches rows ahead of consumption to reduce I/O wait time, particularly beneficial for network sources and slow I/O.

**Enable Read-Ahead:**

```python
from iterable.helpers.detect import open_iterable

# Enable read-ahead with default settings (buffer size: 10 rows)
with open_iterable(
    's3://bucket/data.csv',
    iterableargs={'read_ahead': True}
) as source:
    for row in source:
        process(row)  # Rows are prefetched ahead of consumption
```

**Customize Buffer Size:**

```python
# Larger buffer for better I/O performance (uses more memory)
with open_iterable(
    'data.csv',
    iterableargs={
        'read_ahead': True,
        'read_ahead_size': 50  # Prefetch 50 rows ahead
    }
) as source:
    for row in source:
        process(row)
```

**Customize Refill Threshold:**

```python
# Refill buffer when it drops below 50% capacity (default: 30%)
with open_iterable(
    'data.csv',
    iterableargs={
        'read_ahead': True,
        'read_ahead_size': 20,
        'read_ahead_refill_threshold': 0.5  # Refill at 50%
    }
) as source:
    for row in source:
        process(row)
```

**When to Use Read-Ahead:**

✅ **Network sources**: S3, GCS, Azure Blob Storage  
✅ **Slow I/O**: Network latency, slow disks  
✅ **Sequential processing**: When processing rows one-by-one  
✅ **Predictable access patterns**: Sequential row-by-row reading

❌ **Fast local files**: Overhead may not be worth it  
❌ **Random access**: When skipping rows or random access patterns  
❌ **Memory-constrained**: Uses additional memory for buffer

**Performance Impact:**

- **I/O-bound operations**: Significant improvement (20-50% faster)
- **CPU-bound operations**: Minimal improvement
- **Memory usage**: Adds `read_ahead_size * average_row_size` bytes to memory usage

### Performance Issues

- **Use context managers**: Automatic resource cleanup
- **Use bulk operations**: `write_bulk()` and `read_bulk()` for better performance
- **Use appropriate engine**: DuckDB engine for large CSV/JSONL files
- **Use compression**: Compressed formats often process faster
- **Enable read-ahead**: For network sources and slow I/O (see Read-Ahead Caching above)

## Related Functions

- [`detect_file_type()`](#) - Detect file type and compression
- [`convert()`](/api/convert) - Convert between formats

## See Also

- [Quick Start Guide](/getting-started/quick-start)
- [Basic Usage](/getting-started/basic-usage)
- [BaseIterable Methods](/api/base-iterable)
- [Exception Hierarchy](/api/exceptions) - Comprehensive exception reference
- [Database Engines](/api/database-engines) - Database engine documentation
- [Cloud Storage Support](/api/cloud-storage) - Cloud storage URI support (S3, GCS, Azure)
