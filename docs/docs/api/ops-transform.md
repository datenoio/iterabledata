---
sidebar_position: 10
title: Transform Operations
description: Row and column transformation operations (head, tail, sample, dedup, select, slice)
---

# Transform Operations

The `iterable.ops.transform` module provides functions for transforming data: slicing, sampling, deduplication, selection, and other row/column operations.

## Overview

Transform operations modify your data:
- **Slice rows** (head, tail, by range)
- **Sample randomly** from datasets
- **Remove duplicates** based on key fields
- **Select columns** with optional renaming
- **All operations are streaming-friendly** and memory-efficient

## Functions

### `head()`

Get the first N rows from an iterable dataset.

```python
from iterable.ops import transform

# Get first 10 rows from a file
for row in transform.head("data.csv", n=10):
    print(row)

# Get first 5 rows from an iterable
rows = [{"a": i} for i in range(100)]
first_five = list(transform.head(rows, n=5))
```

**Parameters:**
- `iterable`: An iterable of row dictionaries, or a file path/stream
- `n`: Number of rows to return (default: 10)

**Returns:** Iterator yielding the first N rows

### `tail()`

Get the last N rows from an iterable dataset.

```python
from iterable.ops import transform

# Get last 10 rows from a file
last_rows = transform.tail("data.csv", n=10)

# Get last 5 rows from an iterable
rows = [{"a": i} for i in range(100)]
last_five = transform.tail(rows, n=5)
```

**Parameters:**
- `iterable`: An iterable of row dictionaries, or a file path/stream
- `n`: Number of rows to return (default: 10)

**Returns:** List containing the last N rows

**Note:** For large datasets, this may require iterating through the entire dataset.

### `sample_rows()`

Randomly sample rows from an iterable dataset.

```python
from iterable.ops import transform

# Sample 1000 rows randomly
for row in transform.sample_rows("data.csv", n=1000):
    print(row)

# Reproducible sampling with seed
sampled = list(transform.sample_rows("data.csv", n=100, seed=42))
```

**Parameters:**
- `iterable`: An iterable of row dictionaries, or a file path/stream
- `n`: Number of rows to sample (default: 1000)
- `seed`: Optional random seed for reproducibility

**Returns:** Iterator yielding randomly sampled rows

**Algorithm:** Uses reservoir sampling for efficient sampling without materializing the entire dataset.

### `deduplicate()`

Remove duplicate rows based on specified key fields.

```python
from iterable.ops import transform

# Remove duplicates by email (keep first occurrence)
for row in transform.deduplicate("users.csv", keys=["email"]):
    print(row)

# Keep last occurrence instead
for row in transform.deduplicate("users.csv", keys=["email"], keep="last"):
    print(row)

# Deduplicate by multiple fields
for row in transform.deduplicate("data.csv", keys=["user_id", "date"]):
    print(row)
```

**Parameters:**
- `iterable`: An iterable of row dictionaries, or a file path/stream
- `keys`: List of field names to use for uniqueness (None for all fields)
- `keep`: Which occurrence to keep - "first" (default) or "last"

**Returns:** Iterator of deduplicated row dictionaries

### `select()`

Select specific columns from rows, optionally with renaming.

```python
from iterable.ops import transform

# Select specific fields
for row in transform.select("data.csv", fields=["id", "name", "email"]):
    print(row)  # Only contains id, name, email

# Select and rename fields
for row in transform.select("data.csv", fields={"old_name": "new_name"}):
    print(row)  # Contains "new_name" instead of "old_name"
```

**Parameters:**
- `iterable`: An iterable of row dictionaries, or a file path/stream
- `fields`: List of field names to select, or dict mapping old->new names

**Returns:** Iterator of row dictionaries with only selected fields

### `slice_rows()`

Slice rows by index range.

```python
from iterable.ops import transform

# Get rows 100-199 (inclusive start, exclusive end)
for row in transform.slice_rows("data.csv", start=100, end=200):
    print(row)

# Get all rows from index 500 onwards
for row in transform.slice_rows("data.csv", start=500):
    print(row)
```

**Parameters:**
- `iterable`: An iterable of row dictionaries, or a file path/stream
- `start`: Start index (inclusive, default: 0)
- `end`: End index (exclusive, None for all remaining rows)

**Returns:** Iterator yielding rows in the specified range

## Examples

### Basic Data Sampling

```python
from iterable.ops import transform

# Get a quick preview
first_10 = list(transform.head("large_dataset.csv", n=10))
print("First 10 rows:")
for row in first_10:
    print(row)

# Get a random sample for analysis
sample = list(transform.sample_rows("large_dataset.csv", n=1000, seed=42))
print(f"\nRandom sample: {len(sample)} rows")
```

### Removing Duplicates

```python
from iterable.ops import transform

# Remove duplicate users by email
unique_users = list(transform.deduplicate("users.csv", keys=["email"]))

# Remove duplicates keeping the most recent entry
recent_users = list(transform.deduplicate(
    "users.csv", 
    keys=["email"], 
    keep="last"
))

print(f"Original: {inspect.count('users.csv')} rows")
print(f"After dedup: {len(unique_users)} rows")
```

### Column Selection and Renaming

```python
from iterable.ops import transform

# Select only needed columns
selected = list(transform.select(
    "data.csv",
    fields=["id", "name", "email", "status"]
))

# Rename columns for consistency
renamed = list(transform.select(
    "data.csv",
    fields={
        "user_id": "id",
        "full_name": "name",
        "email_address": "email"
    }
))
```

### Data Slicing

```python
from iterable.ops import transform

# Process data in chunks
chunk_size = 1000
start = 0

while True:
    chunk = list(transform.slice_rows(
        "data.csv",
        start=start,
        end=start + chunk_size
    ))
    
    if not chunk:
        break
    
    # Process chunk
    process_chunk(chunk)
    
    start += chunk_size
```

### Advanced Transformations

```python
from iterable.ops import transform

# Add sequence numbers
rows = transform.enum_field("data.csv", field="seq_id", type="int", start=1)

# Add UUIDs
rows = transform.enum_field("data.csv", field="id", type="uuid")

# Fill missing values
rows = transform.fill_missing("data.csv", field="status", strategy="forward")

# Rename fields
rows = transform.rename_fields("data.csv", {"old_name": "new_name"})

# Explode array/delimited fields
rows = transform.explode("data.csv", field="tags", separator=",")

# Replace values
rows = transform.replace_values("data.csv", field="status", pattern="old", replacement="new")

# Sort rows
rows = transform.sort_rows("data.csv", by=["date", "id"], desc=[True, False])

# Split fields
rows = transform.split("data.csv", field="full_name", separator=" ", into=["first", "last"])

# Fix field lengths
rows = transform.fixlengths("data.csv", lengths={"code": 10, "name": 50})

# Concatenate multiple files
rows = transform.cat("file1.csv", "file2.csv", "file3.csv")
```

### Relational Operations

```python
from iterable.ops import transform

# Join two datasets
joined = transform.join(
    "users.csv",
    "orders.csv",
    on="user_id",
    join_type="left"
)

# Find rows in first but not in second
diff_rows = transform.diff("file1.csv", "file2.csv", keys=["id"])

# Exclude rows matching another dataset
filtered = transform.exclude("all_users.csv", "deleted_users.csv", keys=["id"])
```

### Combining Transformations

```python
from iterable.ops import transform, stats

# Sample, deduplicate, and select
pipeline = transform.sample_rows("large_dataset.csv", n=10000, seed=42)
pipeline = transform.deduplicate(pipeline, keys=["user_id"])
pipeline = transform.select(pipeline, fields=["user_id", "action", "timestamp"])

# Process transformed data
for row in pipeline:
    process(row)

# Or convert to list for analysis
clean_data = list(pipeline)
summary = stats.compute(clean_data)
```

### Working with Iterables

All transform operations work with both file paths and Python iterables:

```python
from iterable.ops import transform
from iterable import open_iterable

# Chain operations on iterables
with open_iterable("data.csv") as source:
    # Sample
    sampled = transform.sample_rows(source, n=1000)
    
    # Deduplicate
    unique = transform.deduplicate(sampled, keys=["id"])
    
    # Select columns
    selected = transform.select(unique, fields=["id", "value"])
    
    # Process
    for row in selected:
        print(row)
```

## Performance Notes

- **`head()`**: Very fast, only reads first N rows
- **`tail()`**: May require full iteration for large datasets
- **`sample_rows()`**: Uses reservoir sampling - memory efficient even for very large datasets
- **`deduplicate()`**: Memory efficient, uses set-based tracking
- **`select()`**: Very fast, just filters dictionary keys
- **`slice_rows()`**: Efficient for ranges, but may need to skip rows before start

## Integration with Pipeline

Transform operations integrate seamlessly with the `pipeline()` framework:

```python
from iterable import pipeline
from iterable.ops import transform

# Use transforms in a pipeline
result = pipeline(
    "data.csv",
    [
        lambda rows: transform.sample_rows(rows, n=1000),
        lambda rows: transform.deduplicate(rows, keys=["id"]),
        lambda rows: transform.select(rows, fields=["id", "value"]),
    ]
)
```

## Advanced Functions

### `enum_field()`

Add sequence numbers or UUIDs to rows.

```python
# Add integer sequence
for row in transform.enum_field("data.csv", field="seq_id", type="int", start=0):
    print(row)

# Add UUIDs
for row in transform.enum_field("data.csv", field="id", type="uuid"):
    print(row)
```

### `reverse()`

Reverse the order of rows (requires materialization).

```python
for row in transform.reverse("data.csv"):
    print(row)
```

### `fill_missing()`

Fill missing/null values using forward fill, backward fill, or constant value.

```python
# Forward fill
for row in transform.fill_missing("data.csv", field="status", strategy="forward"):
    print(row)

# Fill with constant
for row in transform.fill_missing("data.csv", field="category", value="unknown"):
    print(row)
```

### `rename_fields()`

Rename fields in rows.

```python
for row in transform.rename_fields("data.csv", {"old_name": "new_name"}):
    print(row)
```

### `explode()`

Explode array or delimited string fields into multiple rows.

```python
# Explode array field
for row in transform.explode("data.jsonl", field="tags"):
    print(row)

# Explode delimited string
for row in transform.explode("data.csv", field="categories", separator=","):
    print(row)
```

### `replace_values()`

Replace values in fields using exact match or regex.

```python
# Simple replacement
for row in transform.replace_values("data.csv", field="status", pattern="old", replacement="new"):
    print(row)

# Regex replacement
for row in transform.replace_values("data.csv", field="text", pattern=r"\d+", replacement="NUMBER", regex=True):
    print(row)
```

### `sort_rows()`

Sort rows by specified fields (requires materialization).

```python
# Sort by single field
for row in transform.sort_rows("data.csv", by=["date"]):
    print(row)

# Sort by multiple fields
for row in transform.sort_rows("data.csv", by=["status", "id"], desc=[True, False]):
    print(row)
```

### `transpose()`

Transpose rows and columns (requires materialization).

```python
for row in transform.transpose("data.csv"):
    print(row)
```

### `split()`

Split a field into multiple fields.

```python
for row in transform.split("data.csv", field="full_name", separator=" ", into=["first", "last"]):
    print(row)
```

### `fixlengths()`

Fix field lengths by padding or truncating.

```python
for row in transform.fixlengths("data.csv", lengths={"code": 10, "name": 50}):
    print(row)
```

### `cat()`

Concatenate multiple iterables.

```python
for row in transform.cat("file1.csv", "file2.csv", "file3.csv"):
    print(row)
```

### `join()`

Join two iterables based on key fields.

```python
# Inner join
for row in transform.join("users.csv", "orders.csv", on="user_id", join_type="inner"):
    print(row)

# Left join
for row in transform.join("users.csv", "orders.csv", on="user_id", join_type="left"):
    print(row)
```

### `diff()`

Compute set difference (rows in left but not in right).

```python
for row in transform.diff("file1.csv", "file2.csv", keys=["id"]):
    print(row)
```

### `exclude()`

Exclude rows that match keys in another iterable.

```python
for row in transform.exclude("all_users.csv", "deleted_users.csv", keys=["id"]):
    print(row)
```

## Best Practices

1. **Use `head()` for quick previews** - Don't load entire datasets just to see structure
2. **Use `sample_rows()` for large datasets** - Analyze samples before processing full data
3. **Deduplicate early** - Remove duplicates before expensive operations
4. **Select only needed columns** - Reduce memory usage and improve performance
5. **Chain operations** - Combine multiple transforms for efficient processing
6. **Avoid materialization when possible** - Operations like `reverse()`, `sort_rows()`, `transpose()` require full materialization
7. **Use joins efficiently** - Consider using DuckDB for large joins when available
