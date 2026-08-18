---
name: format-implementation
description: Guide for implementing new data formats in IterableData. Use when adding support for new file formats, compression codecs, or extending format capabilities.
---

# Format Implementation Guide

## Adding New Formats

### Step-by-Step Process

1. **Create format file**: `iterable/datatypes/<format>.py`
2. **Implement BaseIterable**: Inherit from `BaseIterable` in `iterable/base.py`
3. **Required methods**: `read()`, `write()`, `read_bulk()`, `write_bulk()`, etc.
4. **Add detection**: Update `iterable/helpers/detect.py`
5. **Create tests**: `tests/test_<format>.py`
6. **Update dependencies**: Add optional dependency to `pyproject.toml` if needed
7. **Update documentation**: Add format to docs

### Implementation Pattern

```python
from iterable.base import BaseIterable

class NewFormatIterable(BaseIterable):
    def __init__(self, source, mode='r', **kwargs):
        super().__init__(source, mode, **kwargs)
        # Initialize format-specific resources
    
    def read(self):
        # Return iterator of dict objects
        pass
    
    def write(self, data):
        # Write dict objects to file
        pass
    
    def read_bulk(self, size=1000):
        # Bulk read for performance
        pass
    
    def write_bulk(self, data):
        # Bulk write for performance
        pass
```

### Format Detection

Update `iterable/helpers/detect.py`:

1. Add file extension detection
2. Add magic number detection (for binary formats)
3. Add content-based heuristics if needed
4. Update `detect_file_type()` function

Example:
```python
def detect_file_type(filename, content=None):
    # Check extension
    if filename.endswith('.newformat'):
        return 'newformat'
    
    # Check magic numbers
    if content and content.startswith(b'MAGIC'):
        return 'newformat'
    
    # ... existing detection logic
```

## Adding New Codecs

### Step-by-Step Process

1. **Create codec file**: `iterable/codecs/<codec>codec.py`
2. **Implement codec class**: `read()`, `write()`, `close()` methods
3. **Add detection**: Update `iterable/helpers/detect.py`
4. **Add compression detection**: Update format detection logic
5. **Create tests**: Add to relevant test file or create new one
6. **Update dependencies**: Add optional dependency to `pyproject.toml`

### Codec Pattern

```python
class NewCodec:
    def __init__(self, fileobj, mode='r'):
        self.fileobj = fileobj
        self.mode = mode
        # Initialize compression library
    
    def read(self, size=-1):
        # Decompress and return data
        pass
    
    def write(self, data):
        # Compress and write data
        pass
    
    def close(self):
        # Clean up resources
        pass
```

## Testing Requirements

### Test File Structure

```python
import pytest
from iterable import open_iterable

class TestNewFormat:
    def test_read(self):
        # Test basic reading
        pass
    
    def test_write(self):
        # Test basic writing
        pass
    
    def test_read_bulk(self):
        # Test bulk operations
        pass
    
    def test_compressed(self):
        # Test with compression (.gz, .bz2, .zst, etc.)
        pass
    
    def test_edge_cases(self):
        # Empty files, malformed data, etc.
        pass
```

### Test Coverage

- Basic read/write operations
- Bulk operations
- Compressed files (if supported)
- Various encodings (for text formats)
- Edge cases: empty files, malformed data
- Missing optional dependencies (should skip gracefully)

## Dependencies

### Optional Dependencies

Add to `pyproject.toml`:

```toml
[project.optional-dependencies]
newformat = ["newformat-library>=1.0.0"]
```

### Import Handling

Handle missing dependencies gracefully:

```python
try:
    import newformat_library
except ImportError:
    raise ImportError(
        "newformat support requires 'newformat-library'. "
        "Install with: pip install iterabledata[newformat]"
    )
```

## Format Capabilities

Implement capability reporting:

```python
def get_capabilities(self):
    return {
        'read': True,
        'write': True,
        'bulk': True,
        'totals': False,  # Can't count rows without reading
        'streaming': True,
        'tables': False,  # Single table format
    }
```

## Examples

Look at existing implementations:
- `iterable/datatypes/csv.py` - Text format example
- `iterable/datatypes/parquet.py` - Binary format example
- `iterable/codecs/gzipcodec.py` - Compression codec example

## Common Pitfalls

- **Memory issues**: Use streaming for large files
- **Encoding**: Handle various text encodings automatically
- **Compression**: Support common codecs (gzip, bz2, zstd, etc.)
- **Error messages**: Provide helpful errors for missing dependencies
- **Context managers**: Always support `with` statements
- **Filename-only formats**: If your format requires a file path and does not support stream or codec, validate in `reset()` (or `__init__`) and raise a clear error (e.g. `ReadError`) when `filename` is None.
- **read_bulk() exhaustion**: When no more records are available, `read_bulk()` MUST return an empty list `[]`; do not raise `StopIteration`.
