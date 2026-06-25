---
sidebar_position: 9
title: Statistics Operations
description: Statistics computation, frequency analysis, and unique value detection
---

# Statistics Operations

The `iterable.ops.stats` module provides functions for computing statistics, frequency analysis, and unique value detection on datasets.

## Overview

Statistics operations help you understand data distributions and patterns:
- **Compute comprehensive statistics** for all fields
- **Analyze frequency distributions** of values
- **Detect unique values** and duplicates
- **Leverage DuckDB** for fast computation on large datasets

## Functions

### `compute()`

Compute comprehensive statistics for all fields in an iterable dataset.

```python
from iterable.ops import stats

# Compute statistics for a file
summary = stats.compute("data.csv", detect_dates=True)
print(summary["price"]["mean"])
print(summary["price"]["stddev"])

# Compute statistics for an iterable
rows = [
    {"value": 1, "name": "a"},
    {"value": 2, "name": "b"},
    {"value": 3, "name": "c"},
]
summary = stats.compute(rows)
```

**Parameters:**
- `iterable`: An iterable of row dictionaries, or a file path/stream
- `detect_dates`: Whether to detect date fields (default: False)
- `engine`: Optional engine to use ('duckdb' for optimization)
- `include_top_values`: When True, include `top_values` (most frequent values with counts) per field (default: False)
- `top_n`: Number of top values to include when `include_top_values` is True (default: 10)
- `dict_threshold`: Unique-to-total ratio at/below which a field is flagged as a dictionary (lookup) field. Defaults to the `DICT_THRESHOLD` environment variable or 0.1.

**Returns:** Dictionary mapping field names to their statistics:
- `count`: Number of non-null values
- `null_count`: Number of null values
- `null_fraction`: Fraction of values that are null (0..1)
- `unique_count`: Number of unique values
- `is_dictionary`: Whether the field behaves as a dictionary/lookup field
- `top_values`: List of `{value, count}` (only when `include_top_values=True`)
- `min`, `max`: Minimum and maximum values (for numeric fields)
- `mean`, `median`, `stddev`: Statistical measures (for numeric fields)
- `min_length`, `max_length`, `avg_length`: String length statistics (for string fields)

**Example Output:**
```python
{
    "price": {
        "count": 1000,
        "null_count": 5,
        "unique_count": 250,
        "min": 10.0,
        "max": 999.99,
        "mean": 245.5,
        "median": 200.0,
        "stddev": 150.2
    },
    "name": {
        "count": 1000,
        "null_count": 0,
        "unique_count": 500,
        "min_length": 3,
        "max_length": 50,
        "avg_length": 12.5
    }
}
```

### `frequency()`

Compute frequency distributions for specified fields.

```python
from iterable.ops import stats

# Frequency analysis for single field
freq = stats.frequency("data.csv", fields=["status"])
print(freq["status"]["active"])  # Count of "active" status

# Frequency analysis for multiple fields
freq = stats.frequency("data.csv", fields=["status", "category"])

# Frequency with limit (top N most frequent)
freq = stats.frequency("data.csv", fields=["status"], limit=10)
```

**Parameters:**
- `iterable`: An iterable of row dictionaries, or a file path/stream
- `fields`: List of field names to analyze (None for all fields)
- `limit`: Optional limit on number of top frequencies to return per field

**Returns:** Dictionary mapping field names to frequency dictionaries (value -> count, sorted by frequency descending)

**Example Output:**
```python
{
    "status": {
        "active": 750,
        "inactive": 200,
        "pending": 50
    },
    "category": {
        "A": 400,
        "B": 300,
        "C": 300
    }
}
```

### `uniq()`

Identify unique rows or unique values for specified fields.

```python
from iterable.ops import stats

# Get unique rows by email
unique_rows = list(stats.uniq("data.csv", fields=["email"]))

# Get unique values only
unique_emails = list(stats.uniq("data.csv", fields=["email"], values_only=True))

# Get unique values with counts
counts = stats.uniq("data.csv", fields=["email"], include_count=True)
print(counts["user@example.com"])  # Count of occurrences
```

**Parameters:**
- `iterable`: An iterable of row dictionaries, or a file path/stream
- `fields`: List of field names to use for uniqueness (None for all fields)
- `values_only`: If True, return only unique values (not full rows)
- `include_count`: If True, include occurrence counts in results

**Returns:**
- If `values_only=True`: Iterator of unique values
- If `include_count=True`: Dictionary mapping unique items to counts
- Otherwise: Iterator of unique rows

## Examples

### Basic Statistics

```python
from iterable.ops import stats

# Compute statistics for all fields
summary = stats.compute("sales.csv", detect_dates=True)

# Access statistics for a field
price_stats = summary["price"]
print(f"Price range: ${price_stats['min']:.2f} - ${price_stats['max']:.2f}")
print(f"Average price: ${price_stats['mean']:.2f}")
print(f"Standard deviation: ${price_stats['stddev']:.2f}")
print(f"Unique prices: {price_stats['unique_count']}")
```

### Frequency Analysis

```python
from iterable.ops import stats

# Find most common status values
freq = stats.frequency("users.csv", fields=["status"], limit=5)

print("Top 5 statuses:")
for status, count in freq["status"].items():
    print(f"  {status}: {count}")

# Analyze multiple fields
freq = stats.frequency("products.csv", fields=["category", "brand"])
for field, frequencies in freq.items():
    print(f"\n{field} distribution:")
    for value, count in list(frequencies.items())[:5]:  # Top 5
        print(f"  {value}: {count}")
```

### Finding Duplicates

```python
from iterable.ops import stats

# Find unique emails
unique_emails = list(stats.uniq("users.csv", fields=["email"], values_only=True))
print(f"Unique emails: {len(unique_emails)}")

# Find duplicate emails with counts
email_counts = stats.uniq("users.csv", fields=["email"], include_count=True)
duplicates = {email: count for email, count in email_counts.items() if count > 1}
print(f"Duplicate emails: {len(duplicates)}")
for email, count in duplicates.items():
    print(f"  {email}: {count} occurrences")
```

### Data Quality Analysis

```python
from iterable.ops import stats

# Analyze data quality
summary = stats.compute("data.csv")

for field, stats_info in summary.items():
    null_pct = (stats_info["null_count"] / 
                (stats_info["count"] + stats_info["null_count"]) * 100)
    
    print(f"{field}:")
    print(f"  Null percentage: {null_pct:.1f}%")
    print(f"  Unique values: {stats_info['unique_count']}")
    
    if "mean" in stats_info:
        print(f"  Range: {stats_info['min']} - {stats_info['max']}")
        print(f"  Mean: {stats_info['mean']:.2f}")
```

### Combining with Other Operations

```python
from iterable.ops import inspect, stats, transform

# Analyze a sample of data
sample = list(transform.sample_rows("large_dataset.csv", n=10000))
summary = stats.compute(sample)

# Get frequency of top categories
freq = stats.frequency(sample, fields=["category"], limit=10)

# Find unique combinations
unique = list(stats.uniq(sample, fields=["user_id", "product_id"]))
print(f"Unique user-product combinations: {len(unique)}")
```

## Performance Notes

- **`compute()`**: For large files, consider using `engine="duckdb"` for significant performance improvements
- **`frequency()`**: Efficient streaming implementation, handles large datasets well
- **`uniq()`**: Memory-efficient for unique value detection, but may require full iteration

## Integration with DuckDB

When available, DuckDB can significantly speed up statistics computation:

```python
from iterable.ops import stats

# Fast statistics with DuckDB (for CSV/JSONL/JSON/Parquet)
try:
    summary = stats.compute("large_file.csv", engine="duckdb")
except Exception:
    # Falls back to Python implementation
    summary = stats.compute("large_file.csv")
```

## Type Detection

The `compute()` function automatically detects field types:

- **Numeric fields**: Get min, max, mean, median, stddev
- **String fields**: Get min_length, max_length, avg_length
- **Date fields**: Enable with `detect_dates=True` for date-specific statistics
