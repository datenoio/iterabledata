---
title: FLEXBUF Format
description: FLEXBUF data format.
---

# FLEXBUF Format

## Description

[What the format is, what it's used for, and why it's useful. Include 2-3 sentences about the format's purpose and common use cases.]

## File Extensions

- `.ext1` - [Description of extension 1]
- `.ext2` - [Alternative extension or alias]

## Implementation Details

### Reading

The FLEXBUF implementation:
- [Key implementation detail 1]
- [Key implementation detail 2]
- [Key implementation detail 3]
- [Any special handling or features]

### Writing

Writing support:
- [Key writing feature 1]
- [Key writing feature 2]
- [Any special considerations]

### Key Features

- **Feature 1**: [Description]
- **Feature 2**: [Description]
- **Feature 3**: [Description]
- **Feature 4**: [Description]

## Usage

```python
from iterable.helpers.detect import open_iterable

# Recommended: Using context manager (automatic cleanup)
# Basic reading
with open_iterable('data.flexbuf') as source:
    for row in source:
        print(row)
# File automatically closed

# Writing (if supported)
with open_iterable('output.flexbuf', mode='w', iterableargs={
    'param1': 'value1'
}) as dest:
    dest.write({'key': 'value'})
# File automatically closed

# Bulk writing (recommended for better performance)
with open_iterable('output.flexbuf', mode='w', iterableargs={
    'param1': 'value1'
}) as dest:
    records = [
        {'key1': 'value1'},
        {'key2': 'value2'}
    ]
    dest.write_bulk(records)
# File automatically closed

# Alternative: Manual close (still supported)
source = open_iterable('data.flexbuf')
try:
    for row in source:
        print(row)
finally:
    source.close()
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `param1` | str | `default` | No | [Description of parameter] |
| `param2` | bool | `True` | No | [Description of parameter] |
| `param3` | int | None | Yes* | [Description of parameter] |

\* [Note about when parameter is required]

## Error Handling

```python
from iterable.helpers.detect import open_iterable

try:
    # Reading with error handling
    with open_iterable('data.flexbuf', iterableargs={
        'param1': 'value1'
    }) as source:
        for row in source:
            process(row)
except FileNotFoundError:
    print("File not found")
except [SpecificError]:
    print("[Error description]")
except Exception as e:
    print(f"Error reading [Format]: {e}")

try:
    # Writing with error handling
    with open_iterable('output.flexbuf', mode='w', iterableargs={
        'param1': 'value1'
    }) as dest:
        dest.write({'key': 'value'})
except Exception as e:
    print(f"Error writing [Format]: {e}")
```

### Common Errors

- **[Error message]**: [Solution or explanation]
- **[Error message]**: [Solution or explanation]
- **[Error message]**: [Solution or explanation]

## Performance Considerations

### Performance Tips

- **Use bulk operations**: Use `write_bulk()` instead of individual `write()` calls for better performance
  ```python
  # Recommended: Bulk write
  with open_iterable('output.flexbuf', mode='w') as dest:
      dest.write_bulk(records)  # Much faster than individual writes
  ```

- **Batch processing**: For large files, process in batches of 10,000-50,000 records
- **Compression**: [Note about compression support and performance]
- **[Format-specific tip]**: [Any format-specific performance considerations]

## Limitations

1. **Limitation 1**: [Description]
2. **Limitation 2**: [Description]
3. **Limitation 3**: [Description]
4. **Dependency**: [If format requires specific package, mention it here]

## Compression Support

FLEXBUF files can be compressed with all supported codecs:
- GZip (`.flexbuf.gz`)
- BZip2 (`.flexbuf.bz2`)
- LZMA (`.flexbuf.xz`)
- LZ4 (`.flexbuf.lz4`)
- ZIP (`.flexbuf.zip`)
- Brotli (`.flexbuf.br`)
- ZStandard (`.flexbuf.zst`)

[Note about compression if format has special considerations]

## Use Cases

- **Use case 1**: [Description]
- **Use case 2**: [Description]
- **Use case 3**: [Description]
- **Use case 4**: [Description]

## Installation

[If format requires optional dependency, include installation instructions:]

```bash
pip install [package-name]
```

## Related Formats

See the [supported formats index](/formats/).

## Troubleshooting

### Common Issues

**Issue**: [Common problem description]
- **Solution**: [How to fix it]

**Issue**: [Another common problem]
- **Solution**: [How to fix it]

**Issue**: [Performance issue]
- **Solution**: [Performance optimization tip]

## Example: [Specific Use Case]

```python
from iterable.helpers.detect import open_iterable

# [Description of what this example does]
with open_iterable('data.flexbuf', iterableargs={
    'param1': 'value1'
}) as source:
    for row in source:
        # [Processing logic]
        print(row)
```

