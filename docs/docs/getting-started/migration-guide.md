---
sidebar_position: 5
title: Migration Guide
description: Guide for upgrading between versions of Iterable Data
---

# Migration Guide

This guide helps you migrate your code when upgrading between versions of Iterable Data.

## Version 1.0.7 and Later

### Exception Hierarchy Improvements

**What Changed**: IterableData now uses a comprehensive exception hierarchy instead of generic `ValueError`, `NotImplementedError`, and `Exception`. This allows for more specific error handling and better error messages.

**Before**:
```python
from iterable import open_iterable

try:
    with open_iterable('data.parquet', mode='w') as dest:
        dest.write({'key': 'value'})
except NotImplementedError:
    print("Writing not supported")
except ValueError as e:
    print(f"Error: {e}")  # Generic error, hard to handle specifically
except Exception as e:
    print(f"Unexpected error: {e}")
```

**After (Recommended)**:
```python
from iterable import open_iterable
from iterable.exceptions import (
    WriteNotSupportedError,
    FormatParseError,
    ReadError,
    IterableDataError
)

try:
    with open_iterable('data.parquet', mode='w') as dest:
        dest.write({'key': 'value'})
except WriteNotSupportedError as e:
    print(f"Writing to {e.format_id} not supported: {e.reason}")
    # Handle unsupported write operation
except FormatParseError as e:
    print(f"Parse error in {e.format_id} at row {e.row_number}: {e.message}")
    # Handle parsing errors with context
except ReadError as e:
    print(f"Read error: {e.message}")
    # Handle read errors
except IterableDataError as e:
    # Catch all IterableData errors
    print(f"IterableData error: {e.message}")
    if e.error_code:
        print(f"Error code: {e.error_code}")
```

**Migration Steps**:
1. **Import specific exceptions**: Import the exceptions you need from `iterable.exceptions`
2. **Update exception handlers**: Replace generic `ValueError`/`Exception` catches with specific exception types
3. **Use error codes**: Check `error_code` attribute for programmatic error handling
4. **Access exception attributes**: Use format-specific attributes like `format_id`, `row_number`, `byte_offset`, etc.

**Exception Mapping**:
- `NotImplementedError` → `WriteNotSupportedError` (for write operations)
- `NotImplementedError` → `FormatNotSupportedError` (for unsupported formats)
- `ValueError` (format parsing) → `FormatParseError`
- `ValueError` (resource requirements) → `ReadError` or `WriteError`
- `ValueError` (format detection) → `FormatDetectionError`
- Generic `Exception` → Specific exception types based on context

**Benefits**:
- **Better error handling**: Catch specific error types programmatically
- **Richer error context**: Access row numbers, byte offsets, format IDs, etc.
- **Error codes**: Use error codes for programmatic handling
- **Backward compatible**: Old code still works, but new code can be more specific

**Example: Handling Format-Specific Errors**:
```python
from iterable import open_iterable
from iterable.exceptions import FormatParseError

try:
    with open_iterable('data.csv') as source:
        for row in source:
            process(row)
except FormatParseError as e:
    # Access detailed error information
    print(f"Failed to parse {e.format_id} format")
    if e.filename:
        print(f"File: {e.filename}")
    if e.row_number:
        print(f"Row: {e.row_number}")
    if e.byte_offset:
        print(f"Byte offset: {e.byte_offset}")
    if e.original_line:
        print(f"Problematic line: {e.original_line}")
    # Handle or log the error appropriately
```

**Example: Using Error Codes**:
```python
from iterable import open_iterable
from iterable.exceptions import IterableDataError

try:
    with open_iterable('data.unknown') as source:
        pass
except IterableDataError as e:
    if e.error_code == "FORMAT_DETECTION_FAILED":
        # Try with explicit format
        with open_iterable('data.unknown', format='csv') as source:
            pass
    elif e.error_code == "FORMAT_NOT_SUPPORTED":
        # Install missing dependencies or use different format
        print(f"Format not supported: {e.message}")
    else:
        # Handle other errors
        print(f"Error: {e.message}")
```

### Context Manager Support

**What Changed**: Iterable Data now supports Python's context manager protocol (`with` statements).

**Before (Still Supported)**:
```python
from iterable import open_iterable

source = open_iterable('data.csv')
try:
    for row in source:
        process(row)
finally:
    source.close()
```

**After (Recommended)**:
```python
from iterable import open_iterable

# Recommended: Using context manager
with open_iterable('data.csv') as source:
    for row in source:
        process(row)
# File automatically closed
```

**Migration Steps**:
1. Replace `try/finally` blocks with `with` statements
2. Remove manual `close()` calls when using context managers
3. Old code still works - migration is optional but recommended

**Benefits**:
- Cleaner, more Pythonic code
- Automatic resource cleanup
- Better error handling

## Version 1.0.6

### Enhanced Documentation

**What Changed**: Comprehensive documentation improvements with better examples and API reference.

**Action Required**: Review updated documentation for best practices and new patterns.

### Improved Examples

**What Changed**: All examples updated to show best practices.

**Action Required**: Update your code to follow new patterns shown in documentation.

## Version 1.0.5

### DuckDB Engine Support

**What Changed**: Added optional DuckDB engine for high-performance querying.

**Before**:
```python
from iterable import open_iterable

source = open_iterable('data.csv.gz')
for row in source:
    process(row)
source.close()
```

**After (Optional Enhancement)**:
```python
from iterable import open_iterable

# Use DuckDB engine for better performance on large files
with open_iterable('data.csv.gz', engine='duckdb') as source:
    total = source.totals()  # Fast row counting
    for row in source:
        process(row)
```

**Migration Steps**:
1. Install DuckDB: `pip install duckdb`
2. Add `engine='duckdb'` parameter when opening supported formats
3. Old code continues to work with internal engine

**Benefits**:
- Faster queries on large CSV/JSONL files
- Fast row counting
- SQL-like operations

### Pipeline Processing Framework

**What Changed**: Added `pipeline()` function for data transformation workflows.

**Before**:
```python
from iterable import open_iterable

source = open_iterable('input.csv')
destination = open_iterable('output.jsonl', mode='w')

for row in source:
    transformed = transform(row)
    destination.write(transformed)

source.close()
destination.close()
```

**After (Optional Enhancement)**:
```python
from iterable import open_iterable
from iterable.pipeline import pipeline

with open_iterable('input.csv') as source:
    with open_iterable('output.jsonl', mode='w') as destination:
        def transform_record(record, state):
            return transform(record)
        
        pipeline(
            source=source,
            destination=destination,
            process_func=transform_record
        )
```

**Migration Steps**:
1. Import `pipeline` from `iterable.pipeline.core`
2. Refactor transformation logic into `process_func`
3. Use pipeline for progress tracking and error handling

**Benefits**:
- Built-in progress tracking
- Error handling framework
- State management
- Cleaner code structure

### Bulk Operations Support

**What Changed**: Enhanced support for bulk read/write operations.

**Before**:
```python
from iterable import open_iterable

dest = open_iterable('output.jsonl', mode='w')
for record in records:
    dest.write(record)
dest.close()
```

**After (Recommended)**:
```python
from iterable import open_iterable

with open_iterable('output.jsonl', mode='w') as dest:
    dest.write_bulk(records)  # Much faster
```

**Migration Steps**:
1. Collect records into batches
2. Use `write_bulk()` instead of individual `write()` calls
3. Use `read_bulk()` for reading multiple records

**Benefits**:
- Significantly better performance
- Reduced I/O operations
- Better memory efficiency

## General Migration Tips

### Testing Your Migration

1. **Test with small files first**: Verify migration works with small test files
2. **Compare outputs**: Ensure migrated code produces same results
3. **Check performance**: Verify performance improvements (if applicable)
4. **Test error handling**: Ensure error handling still works correctly

### Backward Compatibility

- **Old code still works**: Most changes are additive, not breaking
- **Gradual migration**: You can migrate incrementally
- **No forced changes**: Old patterns remain supported

### Common Migration Patterns

#### Pattern 1: Adding Context Managers

```python
# Old
source = open_iterable('data.csv')
try:
    for row in source:
        process(row)
finally:
    source.close()

# New
with open_iterable('data.csv') as source:
    for row in source:
        process(row)
```

#### Pattern 2: Using Bulk Operations

```python
# Old
dest = open_iterable('output.jsonl', mode='w')
for record in records:
    dest.write(record)
dest.close()

# New
with open_iterable('output.jsonl', mode='w') as dest:
    dest.write_bulk(records)
```

#### Pattern 3: Adding DuckDB Engine

```python
# Old
source = open_iterable('large_data.csv.gz')
for row in source:
    process(row)
source.close()

# New (optional, for better performance)
with open_iterable('large_data.csv.gz', engine='duckdb') as source:
    total = source.totals()  # Fast counting
    for row in source:
        process(row)
```

#### Pattern 4: Using Factory Methods

```python
# Old: Traditional initialization
from iterable.datatypes.csv import CSVIterable

source = CSVIterable(filename='data.csv', mode='r', encoding='utf-8')
try:
    for row in source:
        process(row)
finally:
    source.close()

# New: Factory method (optional, clearer intent)
from iterable.datatypes.csv import CSVIterable

with CSVIterable.from_file('data.csv', encoding='utf-8') as source:
    for row in source:
        process(row)
```

#### Pattern 5: Adding Type Hints

```python
# Old: No type hints
def process_csv(filename):
    with open_iterable(filename) as source:
        return [row for row in source]

# New: With type hints (optional, improves IDE support)
from typing import Any
from iterable import open_iterable

def process_csv(filename: str) -> list[dict[str, Any]]:
    with open_iterable(filename) as source:
        return [row for row in source]
```

## Version 1.1.0 and Later (Architecture Improvements)

### Factory Methods for Initialization

**What Changed**: Added factory methods (`from_file()`, `from_stream()`, `from_codec()`) for clearer initialization. The traditional `__init__()` method remains fully supported for backward compatibility.

**Before**:
```python
from iterable.datatypes.csv import CSVIterable

# Traditional initialization
source = CSVIterable(filename='data.csv', mode='r', encoding='utf-8')
```

**After (Optional Enhancement)**:
```python
from iterable.datatypes.csv import CSVIterable

# Factory method - clearer intent
source = CSVIterable.from_file('data.csv', encoding='utf-8')

# Or with stream
import io
stream = io.StringIO("id,name\n1,test\n")
source = CSVIterable.from_stream(stream)
```

**Migration Steps**:
1. Factory methods are **optional** - old code continues to work
2. Use factory methods for clearer code intent
3. Factory methods provide better validation and error messages
4. All factory methods support the same `options` parameter

**Benefits**:
- Clearer API - intent is explicit (`from_file` vs `from_stream`)
- Better validation - errors caught earlier
- Protected attributes - prevents accidental overrides
- Backward compatible - old code still works

### Type Hint Improvements

**What Changed**: Comprehensive type hints added throughout the library. This improves IDE support and static type checking but doesn't affect runtime behavior.

**Before**:
```python
# No type hints - unclear what types are expected
def process_file(filename):
    source = open_iterable(filename)
    return list(source)
```

**After (Optional Enhancement)**:
```python
from typing import Any
from iterable import open_iterable

# Type hints improve IDE support and static checking
def process_file(filename: str) -> list[dict[str, Any]]:
    with open_iterable(filename) as source:
        return list(source)
```

**Migration Steps**:
1. **No code changes required** - type hints are additive
2. Use type hints in your code for better IDE support
3. Run `mypy` for static type checking (optional)
4. Type hints help catch errors before runtime

**Benefits**:
- Better IDE autocomplete and error detection
- Static type checking with `mypy`
- Self-documenting code
- No runtime impact

### Improved Initialization Validation

**What Changed**: Better validation of initialization parameters, including protection against overriding internal attributes.

**Before**:
```python
# Could accidentally override internal attributes
source = CSVIterable(filename='data.csv', options={'stype': 'invalid'})
# Might cause unexpected behavior
```

**After**:
```python
# Protected attributes prevent accidental overrides
try:
    source = CSVIterable.from_file('data.csv', options={'stype': 'invalid'})
except ValueError as e:
    print(f"Error: {e}")  # Clear error message
```

**Migration Steps**:
1. **No changes required** - validation is automatic
2. If you see `ValueError: Cannot override protected attribute`, remove that parameter from `options`
3. Use public API methods instead of trying to override internal state

**Benefits**:
- Prevents accidental bugs
- Clearer error messages
- More robust initialization

## Breaking Changes

### None in Recent Versions

All recent versions maintain backward compatibility. The changes in Phase 3 (factory methods, type hints, improved validation) are **additive** and don't break existing code:

- ✅ Old initialization patterns still work
- ✅ No API changes that break existing code
- ✅ Type hints are optional and don't affect runtime
- ✅ Factory methods are optional enhancements

If you encounter any issues:

1. Check the [CHANGELOG](https://github.com/datenoio/iterabledata/blob/main/CHANGELOG.md) for detailed changes
2. Review [Troubleshooting Guide](troubleshooting.md) for solutions
3. Report issues on GitHub

## Getting Help

If you need help with migration:

1. **Check documentation**: Review updated guides and examples
2. **Review examples**: Check use case examples for patterns
3. **Test incrementally**: Migrate one feature at a time
4. **Ask for help**: Open an issue on GitHub if you encounter problems

## Related Topics

- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions
- [Best Practices](best-practices.md) - Recommended patterns
- [API Reference](/api/open-iterable) - Full API documentation
- [CHANGELOG](https://github.com/datenoio/iterabledata/blob/main/CHANGELOG.md) - Detailed version history

