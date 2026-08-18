## sidebar_position: 4
title: Troubleshooting
description: Common issues and solutions when using Iterable Data

# Troubleshooting

This guide helps you resolve common issues when using Iterable Data.

## General Issues

### File Not Found Errors

**Error**: `FileNotFoundError: [Errno 2] No such file or directory`

**Solutions**:

- Verify the file path is correct (use absolute paths if relative paths don't work)
- Check file permissions - ensure you have read access
- For compressed files, ensure the file extension matches the compression type
- Use `os.path.exists()` to verify file exists before opening

```python
import os
from iterable import open_iterable

file_path = 'data.csv.gz'
if os.path.exists(file_path):
    with open_iterable(file_path) as source:
        for row in source:
            print(row)
else:
    print(f"File not found: {file_path}")
```

### Encoding Errors

**Error**: `UnicodeDecodeError: 'utf-8' codec can't decode byte...`

**Solutions**:

- Specify encoding explicitly in `iterableargs`
- Try common encodings: `latin-1`, `cp1252`, `iso-8859-1`
- Use encoding detection utilities

```python
from iterable import open_iterable
from iterable.helpers.utils import detect_encoding

# Detect encoding first
encoding_info = detect_encoding('data.csv')
print(f"Detected encoding: {encoding_info['encoding']}")

# Use detected encoding
with open_iterable('data.csv', iterableargs={
    'encoding': encoding_info['encoding']
}) as source:
    for row in source:
        print(row)
```

### Memory Issues

**Error**: `MemoryError` or system runs out of memory

**Solutions**:

- Process files in smaller batches
- Use `read_bulk()` with smaller batch sizes
- Use streaming/iterative processing instead of loading all data
- Use compressed formats to reduce memory usage
- Consider using DuckDB engine for large CSV/JSONL files

```python
from iterable import open_iterable

# Process in smaller batches
with open_iterable('large_file.csv') as source:
    batch = []
    for row in source:
        batch.append(row)
        if len(batch) >= 1000:  # Smaller batch size
            process_batch(batch)
            batch = []  # Clear batch to free memory
```

### Format Detection Issues

**Error**: Wrong format detected or format not recognized

**Solutions**:

- Check file extension matches the actual format
- Use `detect_file_type()` to verify format detection
- Specify format explicitly if auto-detection fails
- Check file is not corrupted
  ---

```python
from iterable.helpers.detect import detect_file_type

result = detect_file_type('data.csv.gz')
print(f"Detected type: {result['datatype']}")
print(f"Detected codec: {result['codec']}")
print(f"Success: {result['success']}")
```

## Format-Specific Issues

### CSV Format Issues

**Issue**: Wrong delimiter detected or parsing errors

**Solutions**:

- Use `autodetect=True` to automatically detect delimiter
- Specify delimiter explicitly: `iterableargs={'delimiter': ';'}`
- Check for special characters or encoding issues
- Verify CSV file has proper quoting for fields containing delimiters

```python
from iterable import open_iterable

# Auto-detect delimiter
with open_iterable('data.csv', iterableargs={
    'autodetect': True
}) as source:
    for row in source:
        print(row)
```

**Issue**: Missing headers or wrong column names

**Solutions**:

- Provide `keys` parameter when reading files without headers
- Check first row of CSV file to verify headers
- Use `keys` parameter to specify column names explicitly

```python
with open_iterable('data.csv', iterableargs={
    'keys': ['col1', 'col2', 'col3']  # Specify column names
}) as source:
    for row in source:
        print(row)
```

### JSON/JSONL Format Issues

**Issue**: `JSONDecodeError` - Invalid JSON on a line

**Solutions**:

- Check for malformed JSON in the file
- Verify encoding is correct (should be UTF-8)
- Use line-by-line processing to identify problematic lines
- Validate JSON before processing

```python
import json
from iterable import open_iterable

try:
    with open_iterable('data.jsonl') as source:
        for i, row in enumerate(source):
            # Process row
            pass
except json.JSONDecodeError as e:
    print(f"Invalid JSON on line {e.lineno if hasattr(e, 'lineno') else 'unknown'}")
```

**Issue**: Nested data not preserved

**Solutions**:

- JSON/JSONL formats preserve nested structures by default
- Check that you're not flattening data unintentionally
- Verify output format supports nested data (not CSV/Parquet without flattening)

### Parquet Format Issues

**Issue**: Schema mismatch errors

**Solutions**:

- Use `adapt_schema=True` to automatically adapt schema
- Ensure all records have consistent structure
- Provide `keys` parameter if schema is known
- Check first batch of records for schema consistency

```python
with open_iterable('output.parquet', mode='w', iterableargs={
    'adapt_schema': True,  # Automatically adapt schema
    'batch_size': 10000
}) as dest:
    dest.write_bulk(records)
```

**Issue**: Missing PyArrow dependency

**Solutions**:

- Install PyArrow: `pip install pyarrow`
- Verify installation: `python -c "import pyarrow; print(pyarrow.__version__)"`

### XML Format Issues

**Issue**: "tagname parameter is required"

**Solutions**:

- Always provide `tagname` parameter when reading XML files
- Check XML structure to identify correct tag name
- Use XML viewer to inspect file structure

```python
with open_iterable('data.xml', iterableargs={
    'tagname': 'item'  # Required parameter
}) as source:
    for row in source:
        print(row)
```

**Issue**: Memory errors with large XML files

**Solutions**:

- XML uses iterative parsing but may still use significant memory
- Process in chunks if possible
- Consider converting to a more memory-efficient format first

### Database Format Issues (SQLite/DuckDB)

**Issue**: "Table not found" error

**Solutions**:

- Check table name spelling
- Omit `table` parameter to use first table
- List tables in database to verify table exists
- Ensure write mode is used when creating new tables

**Issue**: "File path required" error

**Solutions**:

- Database formats require file paths, not streams
- Use absolute paths if relative paths don't work
- Ensure file path is a string, not a file object

## Performance Issues

### Slow Reading/Writing

**Solutions**:

- Use bulk operations (`write_bulk()`, `read_bulk()`) instead of individual operations
- Increase batch sizes (10,000-50,000 records)
- Use compressed formats for better I/O performance
- Use DuckDB engine for CSV/JSONL files when appropriate
- Process files in parallel if possible

```python
# Slow: Individual writes
with open_iterable('output.jsonl', mode='w') as dest:
    for record in records:
        dest.write(record)  # Slow

# Fast: Bulk writes
with open_iterable('output.jsonl', mode='w') as dest:
    dest.write_bulk(records)  # Much faster
```

### Slow Format Conversion

**Solutions**:

- Adjust `batch_size` parameter in `convert()` function
- Use appropriate compression for output format
- Monitor progress with `silent=False`
- Consider using pipeline for more control

```python
from iterable.convert import convert

convert(
    'input.jsonl.gz',
    'output.parquet',
    batch_size=50000,  # Larger batch size
    silent=False  # Monitor progress
)
```

## Engine-Specific Issues

### DuckDB Engine Issues

**Issue**: DuckDB not available or ImportError

**Solutions**:

- Install DuckDB: `pip install duckdb`
- Verify installation
- Fallback to internal engine if DuckDB not available

```python
try:
    with open_iterable('data.csv.gz', engine='duckdb') as source:
        for row in source:
            process(row)
except ImportError:
    # Fallback to internal engine
    with open_iterable('data.csv.gz', engine='internal') as source:
        for row in source:
            process(row)
```

**Issue**: Format not supported by DuckDB engine

**Solutions**:

- DuckDB only supports CSV, JSONL, NDJSON, and JSON
- Use internal engine for other formats
- Check compression - only GZIP and ZStandard supported

## Pipeline Issues

### Records Not Being Written

**Solutions**:

- Ensure `process_func` returns a dictionary (not `None`)
- Check `skip_nulls` parameter - if `True`, `None` returns are skipped
- Verify destination file is opened in write mode
- Enable `debug=True` to see exceptions

```python
from iterable.pipeline import pipeline

def transform_record(record, state):
    # Must return dict or None
    if record.get('valid', False):
        return record  # Return dict to write
    return None  # Return None to skip

pipeline(
    source=source,
    destination=destination,
    process_func=transform_record,
    skip_nulls=True,  # Skip None returns
    debug=True  # See errors
)
```

### Pipeline Runs Slowly

**Solutions**:

- Optimize `process_func` - avoid expensive operations
- Reduce `trigger_on` frequency
- Use bulk operations in destination if possible
- Profile your code to identify bottlenecks

## Getting Help

If you're still experiencing issues:

1. **Check the documentation**: Review format-specific documentation for your format
2. **Check error messages**: Error messages often contain helpful information
3. **Enable debug mode**: Use `debug=True` in pipeline or check verbose output
4. **Test with small files**: Reproduce issue with small sample files
5. **Check dependencies**: Verify all required packages are installed
6. **File issues**: Report bugs or ask questions on GitHub

## Factory Method Issues

### Initialization Errors

**Issue**: "ValueError: requires filename, stream, or codec"

**Solutions**:

- Provide exactly one source: filename, stream, or codec
- Don't provide multiple sources at once
- Use factory methods for clearer initialization

```python
from iterable.datatypes.csv import CSVIterable

# ✅ Correct: Use factory method
source = CSVIterable.from_file('data.csv')

# ✅ Correct: Use traditional init
source = CSVIterable(filename='data.csv')

# ❌ Incorrect: Multiple sources
source = CSVIterable(filename='data.csv', stream=some_stream)  # Error!
```

**Issue**: "ValueError: Cannot override protected attribute"

**Solutions**:

- Don't try to override internal attributes via `options`
- Protected attributes include: `stype`, `fobj`, `_on_error`, `_error_log`, etc.
- Use public API methods instead

```python
# ❌ Incorrect: Trying to override protected attribute
source = CSVIterable.from_file('data.csv', options={'stype': 'invalid'})  # Error!

# ✅ Correct: Use public API
source = CSVIterable.from_file('data.csv')  # stype set automatically
```

## Reset Operation Issues

### Stream Not Seekable Error

**Error**: `StreamNotSeekableError: Stream is not seekable (required for reset)`

**Solutions**:

- Check if stream supports seeking before calling `reset()`
- Use file paths instead of non-seekable streams when reset is needed
- Reopen file instead of resetting non-seekable streams

```python
from iterable.exceptions import StreamNotSeekableError

try:
    with open_iterable(stream=sys.stdin) as source:
        source.read()
        source.reset()  # May fail for stdin
except StreamNotSeekableError:
    # Reopen instead of resetting
    with open_iterable('data.csv') as source:
        for row in source:
            process(row)
```

**Issue**: Reset doesn't work as expected

**Solutions**:

- Ensure file/stream is seekable
- Reset before reading, not after closing
- For codec sources, reset may reopen the underlying file

```python
# ✅ Correct: Reset before reading
with open_iterable('data.csv') as source:
    row1 = source.read()
    source.reset()  # Reset to beginning
    row2 = source.read()  # Same as row1

# ❌ Incorrect: Reset after close
source = open_iterable('data.csv')
source.close()
source.reset()  # Error: file is closed
```

## Context Manager Issues

### Resource Leaks

**Issue**: Files not being closed properly

**Solutions**:

- Always use context managers (`with` statements)
- Don't forget to close files manually if not using context managers
- Check for resource leaks in long-running processes

```python
# ✅ Correct: Context manager ensures cleanup
with open_iterable('data.csv') as source:
    for row in source:
        process(row)
# File automatically closed

# ⚠️ Manual close required if not using context manager
source = open_iterable('data.csv')
try:
    for row in source:
        process(row)
finally:
    source.close()  # Must close manually
```

**Issue**: Nested context managers causing issues

**Solutions**:

- Each context manager is independent
- Files are closed when exiting their respective context
- No special handling needed for nested contexts

```python
# ✅ Correct: Nested context managers work fine
with open_iterable('input.csv') as source:
    with open_iterable('output.jsonl', mode='w') as dest:
        for row in source:
            dest.write(row)
# Both files closed automatically
```

## Exception Handling

### Catching Specific Exceptions

Use the exception hierarchy to catch specific error types:

```python
from iterable.exceptions import (
    IterableDataError,
    FormatError,
    FormatParseError,
    FormatNotSupportedError,
    ReadError,
    WriteError,
    WriteNotSupportedError,
    CodecError,
    StreamNotSeekableError,
)

try:
    with open_iterable('data.csv') as source:
        for row in source:
            process(row)
except FormatParseError as e:
    # Handle parsing errors with context
    print(f"Parse error at row {e.row_number}: {e.message}")
    print(f"Original line: {e.original_line}")
except FormatNotSupportedError as e:
    # Handle unsupported format
    print(f"Format {e.format_id} not supported")
except ReadError as e:
    # Handle general read errors
    print(f"Read error: {e.message}")
except IterableDataError as e:
    # Catch all iterable errors
    print(f"Error: {e.message}")
except Exception as e:
    # Catch other errors
    print(f"Unexpected error: {e}")
```

### Error Logging

**Issue**: Errors are being skipped but you want to see them

**Solutions**:

- Use `on_error='raise'` to see errors immediately
- Use `on_error='log'` with `error_log` parameter to log errors
- Use `on_error='skip'` to skip errors silently

```python
# Log errors to file
with open_iterable('data.csv', options={
    'on_error': 'log',
    'error_log': 'errors.log'
}) as source:
    for row in source:
        process(row)

# Raise errors immediately
with open_iterable('data.csv', options={
    'on_error': 'raise'  # Default behavior
}) as source:
    for row in source:
        process(row)
```

## Common Error Messages Reference


| Error Message                                     | Common Cause                          | Solution                                     |
| ------------------------------------------------- | ------------------------------------- | -------------------------------------------- |
| `FileNotFoundError`                               | File doesn't exist                    | Check file path                              |
| `UnicodeDecodeError`                              | Wrong encoding                        | Specify encoding explicitly                  |
| `JSONDecodeError`                                 | Invalid JSON                          | Check file format                            |
| `ValueError: tagname parameter is required`       | Missing XML tag name                  | Provide `tagname` parameter                  |
| `ValueError: requires filename, stream, or codec` | No source provided                    | Provide exactly one source                   |
| `ValueError: Cannot override protected attribute` | Trying to override internal attribute | Use public API instead                       |
| `StreamNotSeekableError`                          | Stream doesn't support seeking        | Use file path or reopen file                 |
| `FormatNotSupportedError`                         | Format not supported                  | Check format support or install dependencies |
| `FormatParseError`                                | Malformed data                        | Check file format and encoding               |
| `WriteNotSupportedError`                          | Format doesn't support writing        | Use read-only format or different format     |
| `CodecNotSupportedError`                          | Compression codec not supported       | Install codec library or use different codec |
| `ImportError: No module named 'duckdb'`           | DuckDB not installed                  | Install with `pip install duckdb`            |
| `ImportError: No module named 'pyarrow'`          | PyArrow not installed                 | Install with `pip install pyarrow`           |
| `MemoryError`                                     | File too large                        | Use smaller batches or streaming             |
| `AttributeError`                                  | Missing key in record                 | Check record structure before accessing      |
| `KeyError`                                        | Missing required field                | Provide all required fields when writing     |


## Debugging Tips

### Enable Debug Mode

Debug mode provides comprehensive logging for troubleshooting format detection, file I/O, parsing, and performance issues.

#### Using Debug Parameter

```python
from iterable import open_iterable

# Enable debug mode for a specific operation
with open_iterable('data.csv', debug=True) as source:
    for row in source:
        process(row)
```

#### Using Environment Variable

Enable debug mode globally via environment variable:

```bash
# Enable debug mode for all operations
export ITERABLEDATA_DEBUG=1

# Or in Python
import os
os.environ['ITERABLEDATA_DEBUG'] = '1'
```

#### Programmatic Debug Mode

```python
from iterable.helpers.debug import enable_debug_mode
import logging

# Enable debug mode with custom configuration
enable_debug_mode(level=logging.DEBUG)

# Now all operations will log debug information
with open_iterable('data.csv') as source:
    for row in source:
        process(row)
```

#### What Debug Mode Logs

Debug mode provides detailed logging for:

- **Format Detection**: Detection steps, extension checks, content-based detection attempts
- **File I/O**: File operations, modes, encoding, errors
- **Parsing**: Row parsing, validation, error context
- **Performance**: Pipeline execution metrics, throughput

**Example Debug Output:**

```
2026-01-28 10:30:45 - iterable.detect - DEBUG - Detecting file type for: data.csv
2026-01-28 10:30:45 - iterable.detect - DEBUG - Extension detection: csv (confidence: 1.0)
2026-01-28 10:30:45 - iterable.io - DEBUG - Opening file: data.csv (mode: r, engine: internal)
2026-01-28 10:30:45 - iterable.io - DEBUG - Successfully opened file: data.csv
2026-01-28 10:30:45 - iterable.parse - DEBUG - Parsing row 1
```

#### Debug Mode in Pipelines

```python
from iterable.pipeline import pipeline

# Enable debug mode in pipeline
result = pipeline(
    source=source,
    destination=destination,
    process_func=transform_func,
    debug=True  # Enable debug logging
)
```

### Enable Verbose Output (Alternative)

For basic Python logging without IterableData-specific debug features:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now you'll see debug messages
with open_iterable('data.csv') as source:
    for row in source:
        process(row)
```

### Test with Small Files

Always test your code with small sample files first:

```python
# Create a small test file
test_data = "id,name\n1,test\n2,test2\n"
with open('test.csv', 'w') as f:
    f.write(test_data)

# Test your code
with open_iterable('test.csv') as source:
    for row in source:
        print(row)  # Verify it works
```

### Check File Format

Verify file format before processing:

```python
from iterable.helpers.detect import detect_file_type

result = detect_file_type('data.csv.gz')
print(f"Format: {result.get('datatype')}")
print(f"Codec: {result.get('codec')}")
print(f"Success: {result.get('success')}")
```

### Verify Dependencies

Check if optional dependencies are installed:

```python
try:
    import duckdb
    print("DuckDB available")
except ImportError:
    print("DuckDB not installed")

try:
    import pyarrow
    print("PyArrow available")
except ImportError:
    print("PyArrow not installed")
```

## Related Topics

- [Basic Usage](/getting-started/basic-usage) - Common usage patterns
- [Performance Guide](/getting-started/performance) - Performance optimization
- [Best Practices](/getting-started/best-practices) - Recommended patterns
- [API Reference](/api/open-iterable) - Full API documentation
- [Exception Reference](/api/exceptions) - Exception hierarchy documentation
- [Format Documentation](/formats/) - Format-specific documentation

