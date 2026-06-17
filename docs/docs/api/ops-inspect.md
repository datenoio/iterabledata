---
sidebar_position: 8
title: Inspection Operations
description: Dataset inspection operations (count, head, tail, headers, sniff, analyze)
---

# Inspection Operations

The `iterable.ops.inspect` module provides functions for inspecting datasets: counting rows, getting samples, detecting headers, sniffing file formats, and analyzing structure.

## Overview

Inspection operations help you understand your data before processing:
- **Count rows** efficiently with DuckDB optimization
- **Get samples** (head/tail) without loading entire dataset
- **Detect structure** (headers, types, metadata)
- **Analyze files** to understand format and encoding

## Functions

### `count()`

Count the total number of rows in an iterable dataset.

```python
from iterable.ops import inspect

# Count rows in a file
total = inspect.count("data.csv")
print(f"Total rows: {total}")

# Count with DuckDB optimization (faster for large files)
total = inspect.count("data.csv", engine="duckdb")

# Count from an iterable
rows = [{"a": 1}, {"a": 2}, {"a": 3}]
count = inspect.count(rows)
```

**Parameters:**
- `iterable`: An iterable of row dictionaries, or a file path/stream
- `engine`: Optional engine to use ('duckdb' for optimization on CSV/JSONL/JSON/Parquet)

**Returns:** Total number of rows as an integer

**Performance:** Uses DuckDB pushdown for fast counting on supported formats when `engine="duckdb"` is specified.

### `head()`

Get the first N rows from an iterable dataset.

```python
from iterable.ops import inspect

# Get first 10 rows from a file
for row in inspect.head("data.csv", n=10):
    print(row)

# Get first 5 rows from an iterable
rows = [{"a": i} for i in range(100)]
first_five = list(inspect.head(rows, n=5))
```

**Parameters:**
- `iterable`: An iterable of row dictionaries, or a file path/stream
- `n`: Number of rows to return (default: 10)

**Returns:** Iterator yielding the first N rows

**Note:** The original iterable is not fully consumed beyond the first N rows.

### `tail()`

Get the last N rows from an iterable dataset.

```python
from iterable.ops import inspect

# Get last 10 rows from a file
last_rows = inspect.tail("data.csv", n=10)

# Get last 5 rows from an iterable
rows = [{"a": i} for i in range(100)]
last_five = inspect.tail(rows, n=5)
```

**Parameters:**
- `iterable`: An iterable of row dictionaries, or a file path/stream
- `n`: Number of rows to return (default: 10)

**Returns:** List containing the last N rows

**Note:** For large datasets, this may require iterating through the entire dataset to find the last N rows.

### `headers()`

Get column names (headers) from an iterable dataset.

```python
from iterable.ops import inspect

# Get headers from a file
columns = inspect.headers("data.csv")
print(f"Columns: {columns}")

# Get headers from an iterable
rows = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
headers = inspect.headers(rows)
# Returns: ["a", "b"]
```

**Parameters:**
- `iterable`: An iterable of row dictionaries, or a file path/stream
- `limit`: Optional limit on number of rows to examine (default: None, uses first row)

**Returns:** List of column names (field names)

### `sniff()`

Detect file format, encoding, compression, and other metadata from a file path.

```python
from iterable.ops import inspect

# Sniff CSV file
info = inspect.sniff("data.csv")
print(f"Format: {info['format']}")
print(f"Encoding: {info['encoding']}")
print(f"Delimiter: {info.get('delimiter')}")

# Sniff compressed JSONL file
info = inspect.sniff("data.jsonl.gz")
print(f"Format: {info['format']}")  # "jsonl"
print(f"Compression: {info['compression']}")  # "gzip"
```

**Parameters:**
- `filename`: Path to the file to analyze

**Returns:** Dictionary containing:
- `format`: Detected format (e.g., "csv", "jsonl")
- `encoding`: Detected encoding (e.g., "utf-8")
- `delimiter`: Detected delimiter for CSV (e.g., ",")
- `compression`: Detected compression (e.g., "gzip" or None)
- `has_header`: Boolean indicating if header row exists (for CSV)

### `analyze()`

Analyze dataset structure, field types, and generate metadata.

```python
from iterable.ops import inspect

# Analyze a file
analysis = inspect.analyze("data.csv", sample_size=10000)
print(f"Fields: {list(analysis['fields'].keys())}")
print(f"Row count: {analysis['row_count']}")

# Analyze an iterable
rows = [{"a": 1, "b": "test"}, {"a": 2, "b": "test2"}]
analysis = inspect.analyze(rows)
print(analysis["fields"]["a"]["type"])  # "int"
print(analysis["fields"]["b"]["type"])  # "str"
```

# Analyze with AI documentation (requires iterabledata[ai])
analysis = inspect.analyze(
    "data.csv",
    autodoc=True,
    autodoc_provider="openai",
    autodoc_model="gpt-4o-mini",
)
print(analysis["documentation"])
print(analysis["documentation_meta"])
```

**Parameters:**
- `iterable`: An iterable of row dictionaries, or a file path/stream
- `autodoc`: Whether to include AI-powered documentation (requires `iterabledata[ai]`, default: False)
- `sample_size`: Number of rows to sample for analysis (default: 10000)
- `autodoc_provider`: LLM provider when `autodoc=True` (default: `"openai"`)
- `autodoc_model`: Model name when `autodoc=True`
- `autodoc_format`: Documentation output format when `autodoc=True` (default: `"json"`)
- `include_field_descriptions`: Per-field AI descriptions when `autodoc=True`
- Additional keyword arguments are forwarded to `iterable.ai.doc.generate()`

**Returns:** Dictionary containing:
- `row_count`: Total number of rows (if calculable, None if exceeds sample_size)
- `fields`: Dictionary mapping field names to metadata:
  - `type`: Inferred type (str, int, float, bool, etc.)
  - `nullable`: Whether field contains null values
  - `sample_values`: Sample values from the dataset
  - `description`: AI-generated field description when `autodoc=True` and field descriptions enabled
- `structure`: Overall structure information:
  - `field_count`: Number of fields
  - `analyzed_rows`: Number of rows analyzed
- `documentation`: Generated documentation text when `autodoc=True`
- `documentation_meta`: Provider, model, format, and token usage when `autodoc=True`

See also: [AI-Powered Documentation](ai.md).

## Examples

### Quick Dataset Overview

```python
from iterable.ops import inspect

# Get quick overview of a dataset
filename = "data.csv"

# Count rows
total = inspect.count(filename)
print(f"Total rows: {total}")

# Get headers
columns = inspect.headers(filename)
print(f"Columns ({len(columns)}): {columns}")

# Get first few rows
print("\nFirst 5 rows:")
for row in inspect.head(filename, n=5):
    print(row)

# Analyze structure
analysis = inspect.analyze(filename)
print(f"\nField types:")
for field, info in analysis["fields"].items():
    print(f"  {field}: {info['type']} (nullable: {info['nullable']})")
```

### File Format Detection

```python
from iterable.ops import inspect

# Detect file format and properties
info = inspect.sniff("mystery_file.csv.gz")

if info["format"] == "csv":
    print(f"CSV file with delimiter: {info.get('delimiter', ',')}")
    print(f"Has header: {info.get('has_header', False)}")

if info["compression"]:
    print(f"Compressed with: {info['compression']}")

print(f"Encoding: {info['encoding']}")
```

### Efficient Counting with DuckDB

```python
from iterable.ops import inspect

# Fast counting for large files
large_file = "huge_dataset.csv"

# Without DuckDB (slower, but works for all formats)
count_slow = inspect.count(large_file)

# With DuckDB (much faster for CSV/JSONL/JSON/Parquet)
try:
    count_fast = inspect.count(large_file, engine="duckdb")
    print(f"Fast count: {count_fast}")
except Exception:
    # Falls back to Python iteration if DuckDB unavailable
    count_fast = inspect.count(large_file)
```

## Performance Notes

- **`count()`**: Use `engine="duckdb"` for 10-100x speedup on large CSV/JSONL/JSON/Parquet files
- **`head()`**: Very fast, only reads first N rows
- **`tail()`**: May require full iteration for large datasets (consider using DuckDB for better performance)
- **`analyze()`**: Uses sampling (default 10,000 rows) to maintain performance on large datasets

## Integration with Other Operations

Inspection operations work seamlessly with other iterabledata operations:

```python
from iterable.ops import inspect, stats, transform

# Count and analyze
total = inspect.count("data.csv")
analysis = inspect.analyze("data.csv")

# Use analysis results for statistics
if analysis["row_count"] and analysis["row_count"] < 100000:
    summary = stats.compute("data.csv")
    print(summary)
```
