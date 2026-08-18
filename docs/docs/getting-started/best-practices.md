---
sidebar_position: 6
title: Best Practices
description: Recommended patterns and practices for using Iterable Data effectively
---

# Best Practices

This guide covers recommended patterns and practices for using Iterable Data effectively in production code.

## Resource Management

IterableData manages various resources including file handles, codecs, compression streams, and database connections. Proper resource management is critical to prevent leaks and ensure reliable operation.

### Use Context Managers

**✅ Recommended**: Always use context managers (`with` statements) for automatic resource cleanup.

```python
from iterable import open_iterable

# Recommended: Automatic cleanup
with open_iterable('data.csv') as source:
    for row in source:
        process(row)
# File automatically closed, codecs cleaned up
```

**❌ Avoid**: Manual file management without proper cleanup.

```python
# Not recommended: Manual close required
source = open_iterable('data.csv')
for row in source:
    process(row)
# Easy to forget close() - resource leak!
```

### Resource Cleanup Patterns

IterableData automatically manages resources based on the source type:

#### File-Based Sources

File handles are automatically closed when:
- Exiting a context manager (`with` statement)
- Calling `close()` explicitly
- An exception occurs within a context manager

```python
from iterable import open_iterable

# Context manager ensures cleanup even on exceptions
try:
    with open_iterable('data.csv') as source:
        for row in source:
            process(row)
            if error_condition:
                raise ValueError("Processing error")
except ValueError:
    pass
# File is still closed even though exception occurred
```

#### Codec-Based Sources (Compressed Files)

For compressed files (`.gz`, `.bz2`, `.xz`, `.zst`, etc.), IterableData manages:
1. **Text wrapper** (if text mode): Flushed and closed first
2. **Codec stream**: Closed to finalize compression/decompression
3. **Underlying file**: Closed automatically

```python
# Compressed file - all layers cleaned up automatically
with open_iterable('data.csv.gz') as source:
    for row in source:
        process(row)
# Text wrapper, codec, and file all properly closed
```

#### Stream-Based Sources

External streams (e.g., `sys.stdin`, network streams) are **not closed** by IterableData, as they're managed externally:

```python
import sys
from iterable import open_iterable

# Stream is not closed - managed externally
with open_iterable(stream=sys.stdin) as source:
    for row in source:
        process(row)
# sys.stdin remains open and usable
```

### Reset Operations and Seekability

The `reset()` method requires seekable streams. Non-seekable streams (e.g., network streams, stdin) will raise `ReadError` with error code `STREAM_NOT_SEEKABLE`:

```python
from iterable import open_iterable
from iterable.exceptions import ReadError

try:
    with open_iterable('data.csv') as source:
        source.read()
        source.reset()  # Requires seekable stream
except ReadError as e:
    if e.error_code == "STREAM_NOT_SEEKABLE":
        print("Cannot reset: stream is not seekable")
        # Alternative: Reopen the file
        source = open_iterable('data.csv')
```

**Best Practice**: Check if reset is needed before calling it, or handle the exception gracefully.

### Multiple Close Calls

The `close()` method is **idempotent** - calling it multiple times is safe:

```python
source = open_iterable('data.csv')
source.close()
source.close()  # Safe - no error raised
source.close()  # Still safe
```

### Nested Context Managers

You can safely nest context managers for multiple files:

```python
with open_iterable('input.csv') as source:
    with open_iterable('output.jsonl', mode='w') as dest:
        for row in source:
            dest.write(row)
    # dest closed here
# source closed here
```

### Resource Cleanup on Exceptions

Resources are **always** cleaned up, even when exceptions occur:

```python
try:
    with open_iterable('data.csv') as source:
        for row in source:
            if should_fail:
                raise RuntimeError("Processing failed")
            process(row)
except RuntimeError:
    # File is still properly closed
    pass
```

### Error Log Files

If error logging is enabled, error log files are also automatically cleaned up:

```python
with open_iterable('data.csv', iterableargs={
    'error_log': 'errors.jsonl'
}) as source:
    for row in source:
        process(row)
# Error log file is closed automatically
```

### Handle Errors Properly

**✅ Recommended**: Always wrap file operations in try/except blocks and use specific exception types.

```python
from iterable import open_iterable
from iterable.exceptions import (
    FormatDetectionError,
    FormatNotSupportedError,
    FormatParseError,
    ReadError,
    WriteError,
    IterableDataError
)

try:
    with open_iterable('data.csv') as source:
        for row in source:
            process(row)
except FormatDetectionError as e:
    print(f"Could not detect format: {e.reason}")
    # Try with explicit format
    with open_iterable('data.csv', format='csv') as source:
        for row in source:
            process(row)
except FormatNotSupportedError as e:
    print(f"Format '{e.format_id}' not supported: {e.reason}")
    # Install dependencies or use different format
except FormatParseError as e:
    print(f"Parse error at row {e.row_number}: {e.message}")
    if e.original_line:
        print(f"Problematic line: {e.original_line}")
    # Handle or skip malformed data
except ReadError as e:
    print(f"Read error: {e.message}")
    # Handle read errors
except IterableDataError as e:
    # Catch all IterableData errors
    print(f"IterableData error: {e.message}")
    if e.error_code:
        print(f"Error code: {e.error_code}")
except FileNotFoundError:
    print("File not found")
except Exception as e:
    print(f"Unexpected error: {e}")
```

**❌ Avoid**: Ignoring potential errors or using overly generic exception handlers.

```python
# Not recommended: No error handling
with open_iterable('data.csv') as source:
    for row in source:
        process(row)  # May fail silently

# Not recommended: Too generic
try:
    with open_iterable('data.csv') as source:
        for row in source:
            process(row)
except Exception as e:
    print(f"Error: {e}")  # Can't handle specific error types
```

## Performance Optimization

### Use Bulk Operations

**✅ Recommended**: Use `write_bulk()` and `read_bulk()` for better performance.

```python
from iterable import open_iterable

# Recommended: Bulk operations
with open_iterable('output.jsonl', mode='w') as dest:
    dest.write_bulk(records)  # Much faster than individual writes
```

**❌ Avoid**: Individual operations for large datasets.

```python
# Not recommended: Slow for large datasets
with open_iterable('output.jsonl', mode='w') as dest:
    for record in records:
        dest.write(record)  # Slow - many I/O operations
```

### Choose Appropriate Batch Sizes

**✅ Recommended**: Use batch sizes of 10,000-50,000 records for optimal performance.

```python
from iterable import open_iterable

with open_iterable('input.csv') as source:
    with open_iterable('output.jsonl', mode='w') as dest:
        batch = []
        for row in source:
            batch.append(row)
            if len(batch) >= 10000:  # Good batch size
                dest.write_bulk(batch)
                batch = []
        
        if batch:
            dest.write_bulk(batch)
```

**❌ Avoid**: Very small or very large batch sizes.

```python
# Not recommended: Too small (inefficient) or too large (memory issues)
if len(batch) >= 10:  # Too small - many I/O operations
    dest.write_bulk(batch)

if len(batch) >= 1000000:  # Too large - may cause memory issues
    dest.write_bulk(batch)
```

### Use Appropriate Engines

**✅ Recommended**: Use DuckDB engine for large CSV/JSONL files.

```python
from iterable import open_iterable

# Recommended: DuckDB engine for large files
with open_iterable('large_data.csv.gz', engine='duckdb') as source:
    total = source.totals()  # Fast counting
    for row in source:
        process(row)
```

**❌ Avoid**: Using wrong engine for the task.

```python
# Not recommended: Internal engine for very large CSV files
with open_iterable('huge_data.csv.gz', engine='internal') as source:
    # May be slower than DuckDB engine
    for row in source:
        process(row)
```

## Format Selection

### Choose the Right Format

**✅ Recommended**: Select format based on use case.

- **Analytics**: Use Parquet for columnar storage and fast queries
- **Streaming**: Use JSONL for line-by-line processing
- **Compatibility**: Use CSV for maximum compatibility
- **Nested Data**: Use JSON/JSONL to preserve structure

```python
# Analytics use case
with open_iterable('analytics.parquet', mode='w') as dest:
    dest.write_bulk(records)

# Streaming use case
with open_iterable('stream.jsonl.zst', mode='w') as dest:
    dest.write_bulk(records)
```

### Use Compression Appropriately

**✅ Recommended**: Use compression for large files and network transfer.

```python
# Recommended: Compressed formats for large files
with open_iterable('large_data.jsonl.zst', mode='w') as dest:
    dest.write_bulk(records)  # ZStandard compression
```

**Benefits**:
- Reduced storage space
- Faster I/O (less data to read/write)
- Better network transfer

## Data Processing

### Process in Batches

**✅ Recommended**: Process large files in manageable batches.

```python
from iterable import open_iterable

with open_iterable('large_file.csv') as source:
    batch = []
    for row in source:
        batch.append(row)
        if len(batch) >= 10000:
            process_batch(batch)  # Process batch
            batch = []  # Clear for next batch
    
    if batch:
        process_batch(batch)  # Process remaining
```

**❌ Avoid**: Loading entire file into memory.

```python
# Not recommended: May cause memory issues
all_records = []
with open_iterable('huge_file.csv') as source:
    for row in source:
        all_records.append(row)  # May run out of memory

process_all(all_records)
```

### Filter Early

**✅ Recommended**: Filter records as early as possible in the pipeline.

```python
from iterable.pipeline import pipeline

def filter_and_transform(record, state):
    # Filter early
    if record.get('age', 0) < 18:
        return None  # Skip immediately
    
    # Transform only valid records
    return transform(record)
```

**❌ Avoid**: Processing records you'll discard later.

```python
# Not recommended: Process then discard
def transform_all(record, state):
    transformed = expensive_transform(record)
    if transformed.get('age', 0) < 18:
        return None  # Wasted processing
    return transformed
```

## Error Handling

### Handle Format-Specific Errors

**✅ Recommended**: Use FormatParseError for format-specific parsing issues.

```python
from iterable import open_iterable
from iterable.exceptions import FormatParseError

try:
    with open_iterable('data.jsonl') as source:
        for row in source:
            process(row)
except FormatParseError as e:
    # Access detailed error information
    print(f"Parse error in {e.format_id} format")
    if e.filename:
        print(f"File: {e.filename}")
    if e.row_number:
        print(f"Row: {e.row_number}")
    if e.byte_offset:
        print(f"Byte offset: {e.byte_offset}")
    if e.original_line:
        print(f"Problematic line: {e.original_line}")
    # Handle or log appropriately
except UnicodeDecodeError:
    # Handle encoding issues
    print("Encoding error - specify encoding explicitly")
    with open_iterable('data.jsonl', iterableargs={'encoding': 'latin-1'}) as source:
        for row in source:
            process(row)
```

### Use Debug Mode During Development

**✅ Recommended**: Enable debug mode to catch errors early.

```python
from iterable.pipeline import pipeline

pipeline(
    source=source,
    destination=destination,
    process_func=transform_record,
    debug=True  # Show detailed error information
)
```

## Code Organization

### Use Pipeline for Complex Transformations

**✅ Recommended**: Use `pipeline()` for multi-step transformations.

```python
from iterable import open_iterable
from iterable.pipeline import pipeline

with open_iterable('input.csv') as source:
    with open_iterable('output.jsonl', mode='w') as destination:
        def transform_record(record, state):
            # Complex transformation logic
            return transformed_record
        
        def progress_callback(stats, state):
            print(f"Processed {stats['rec_count']} records")
        
        pipeline(
            source=source,
            destination=destination,
            process_func=transform_record,
            trigger_func=progress_callback,
            trigger_on=1000
        )
```

**❌ Avoid**: Complex nested loops and manual state management.

```python
# Not recommended: Manual state management
count = 0
with open_iterable('input.csv') as source:
    with open_iterable('output.jsonl', mode='w') as destination:
        for row in source:
            count += 1
            if count % 1000 == 0:
                print(f"Processed {count} records")
            transformed = transform(row)
            destination.write(transformed)
```

### Separate Concerns

**✅ Recommended**: Separate file I/O from business logic.

```python
# Good: Separation of concerns
def process_record(record):
    """Business logic"""
    return transformed_record

with open_iterable('input.csv') as source:
    with open_iterable('output.jsonl', mode='w') as destination:
        for row in source:
            transformed = process_record(row)
            destination.write(transformed)
```

**❌ Avoid**: Mixing I/O and business logic.

```python
# Not recommended: Mixed concerns
with open_iterable('input.csv') as source:
    with open_iterable('output.jsonl', mode='w') as destination:
        for row in source:
            # Business logic mixed with I/O
            result = complex_calculation(row)
            destination.write(result)
```

## Testing

### Test with Small Files First

**✅ Recommended**: Test your code with small sample files before processing large datasets.

```python
# Test with small file first
with open_iterable('sample_data.csv') as source:
    for row in source:
        result = process(row)
        assert result is not None  # Verify processing works
```

### Validate Data

**✅ Recommended**: Validate data structure and content.

```python
def validate_record(record):
    """Validate record structure"""
    required_fields = ['id', 'name', 'email']
    return all(field in record for field in required_fields)

with open_iterable('data.csv') as source:
    for row in source:
        if validate_record(row):
            process(row)
        else:
            print(f"Invalid record: {row}")
```

## Memory Management

### Process Streamingly

**✅ Recommended**: Process data streamingly to avoid memory issues.

```python
# Recommended: Streaming processing
with open_iterable('large_file.csv') as source:
    for row in source:
        process(row)  # Process one at a time
        # Memory is freed after each iteration
```

**❌ Avoid**: Accumulating all data in memory.

```python
# Not recommended: Load all into memory
all_data = []
with open_iterable('large_file.csv') as source:
    for row in source:
        all_data.append(row)  # May cause memory issues

# Process later
for row in all_data:
    process(row)
```

### ⚠️ Non-Streaming Formats

Some formats **load entire files into memory** before processing. When working with large files (>100MB), be aware of memory limitations:

**Non-streaming formats include:**
- Feed formats (RSS/Atom): `feed`, `rss`, `atom`
- ARFF: `arff`
- HTML: `html`, `htm`
- TOML: `toml`
- HOCON: `hocon`
- EDN: `edn`
- Bencode: `bencode`
- ASN.1: `asn1`
- iCal: `ical`, `ics`
- Turtle RDF: `turtle`, `ttl`
- VCF: `vcf`
- MHTML: `mhtml`
- FlexBuffers: `flexbuffers`
- PC-Axis: `px`
- MVT: `mvt`

**Check streaming capability programmatically:**

```python
from iterable.helpers.capabilities import get_capability

is_streaming = get_capability("html", "streaming")
if not is_streaming:
    print("Warning: HTML format loads entire file into memory")
    # Consider file size before processing
    import os
    file_size = os.path.getsize('data.html')
    if file_size > 100 * 1024 * 1024:  # 100MB
        print("Large file detected - consider using streaming format")
```

**Best practices for non-streaming formats:**

1. **Check file size** before processing large files
2. **Use streaming alternatives** when available (e.g., JSONL instead of JSON for large files)
3. **Convert to streaming formats** first if you need to process large files repeatedly
4. **Monitor memory usage** when processing large non-streaming files

**Conditional streaming formats:**

Some formats support streaming for large files but load small files entirely:
- **JSON**: Streams files >10MB, loads smaller files entirely
- **GeoJSON**: Streams files >10MB, loads smaller files entirely  
- **TopoJSON**: Streams files >10MB, loads smaller files entirely

For very large files, prefer formats that always stream:
- **JSONL/NDJSON**: Always streams line-by-line
- **CSV/TSV**: Always streams row-by-row
- **XML**: Streams with `tagname` parameter
- **Parquet**: Streams in batches

### Use Appropriate Data Structures

**✅ Recommended**: Use efficient data structures for lookups.

```python
# Recommended: Use sets/dicts for fast lookups
lookup_set = set(lookup_ids)  # Fast membership testing

with open_iterable('data.csv') as source:
    for row in source:
        if row['id'] in lookup_set:  # O(1) lookup
            process(row)
```

## Documentation

### Document Your Code

**✅ Recommended**: Add clear documentation to your processing functions.

```python
def transform_user_record(record, state):
    """
    Transform user record for analytics.
    
    Args:
        record: Dictionary containing user data
        state: Pipeline state dictionary
    
    Returns:
        Transformed record dictionary or None to skip
    """
    if not record.get('active', False):
        return None  # Skip inactive users
    
    return {
        'user_id': record['id'],
        'email': record['email'],
        'created_at': record['created_at']
    }
```

## Summary

### Do's ✅

- Use context managers (`with` statements)
- Handle errors properly using specific exception types from `iterable.exceptions`
- Use bulk operations for performance
- Choose appropriate formats and engines
- Process in batches
- Filter early
- Test with small files first
- Document your code

### Don'ts ❌

- Don't forget to close files (use context managers)
- Don't ignore errors - use specific exception types for better error handling
- Don't use individual operations for large datasets
- Don't load entire files into memory
- Don't process records you'll discard
- Don't mix I/O and business logic
- Don't skip validation

## Related Topics

- [Basic Usage](basic-usage.md) - Common usage patterns
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [Migration Guide](migration-guide.md) - Upgrading between versions
- [API Reference](/api/open-iterable) - Full API documentation

