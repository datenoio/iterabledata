---
sidebar_position: 7
title: Performance Guide
description: Performance optimization guide for IterableData
---

# Performance Guide

This guide provides comprehensive performance optimization strategies for IterableData. Learn how to maximize throughput, minimize memory usage, and optimize for different use cases.

## Table of Contents

- [Bulk Operations](#bulk-operations)
- [Memory Management](#memory-management)
- [Format Selection](#format-selection)
- [Compression](#compression)
- [Streaming vs Batch Processing](#streaming-vs-batch-processing)
- [DuckDB Engine](#duckdb-engine)
- [Benchmarking](#benchmarking)

## Bulk Operations

### Use Bulk Read/Write

**Always prefer bulk operations** (`read_bulk()`, `write_bulk()`) over individual operations (`read()`, `write()`) for better performance.

```python
from iterable.helpers.detect import open_iterable

# ✅ Recommended: Bulk operations
with open_iterable('data.csv') as source:
    while True:
        batch = source.read_bulk(num=10000)  # Read 10,000 records at once
        if not batch:
            break
        process_batch(batch)

# ❌ Avoid: Individual operations (10-100x slower)
with open_iterable('data.csv') as source:
    for row in source:  # One record at a time
        process(row)
```

### Optimal Batch Sizes

Recommended batch sizes vary by format and use case:

| Format | Read Batch Size | Write Batch Size | Notes |
|--------|----------------|------------------|-------|
| CSV | 10,000-50,000 | 10,000-50,000 | Larger batches improve I/O efficiency |
| JSONL | 10,000-50,000 | 10,000-50,000 | Line-by-line format benefits from batching |
| Parquet | 1,024-10,000 | 10,000-50,000 | Parquet has built-in batching |
| JSON | N/A | N/A | Entire file loaded (use JSONL for large files) |
| Excel (XLSX) | 1,000-10,000 | 1,000-10,000 | Memory-intensive format |

**Guidelines:**
- **Small files (under 1MB)**: Batch size 1,000-5,000
- **Medium files (1MB-100MB)**: Batch size 10,000-50,000
- **Large files (>100MB)**: Batch size 50,000-100,000
- **Memory-constrained**: Reduce batch size to 1,000-5,000

### Writing Performance

Bulk writing is **significantly faster** than individual writes:

```python
# ✅ Fast: Bulk write (recommended)
records = [{'id': i, 'name': f'Name{i}'} for i in range(100000)]
with open_iterable('output.csv', mode='w') as dest:
    dest.write_bulk(records)  # Single operation

# ❌ Slow: Individual writes (100x slower)
with open_iterable('output.csv', mode='w') as dest:
    for record in records:
        dest.write(record)  # 100,000 individual operations
```

**Performance comparison:**
- Bulk write: ~10-50 MB/s
- Individual writes: ~0.1-0.5 MB/s

## Memory Management

### Streaming Formats

Use **streaming formats** for large files to maintain constant memory usage:

| Format | Streaming | Memory Usage |
|--------|-----------|--------------|
| CSV | ✅ Yes | Constant (~10-50 MB) |
| JSONL | ✅ Yes | Constant (~10-50 MB) |
| Parquet | ✅ Yes | Constant (~50-200 MB) |
| JSON | ⚠️ Conditional* | Scales with file size |
| Excel (XLSX) | ❌ No | Scales with file size |
| XML | ⚠️ Conditional* | Scales with file size |

\* JSON uses streaming parser (`ijson`) for files >10MB. XML uses streaming for large files.

```python
# ✅ Streaming format - constant memory
with open_iterable('large_data.csv.gz') as source:  # 10GB file
    for row in source:  # Memory stays constant
        process(row)

# ⚠️ Non-streaming format - memory scales with file size
with open_iterable('large_data.xlsx') as source:  # 10GB file
    for row in source:  # Entire file loaded into memory!
        process(row)
```

### Memory-Efficient Patterns

**Pattern 1: Process in chunks**
```python
# Process large files in manageable chunks
with open_iterable('large.csv') as source:
    chunk_size = 10000
    while True:
        batch = source.read_bulk(chunk_size)
        if not batch:
            break
        # Process batch, then it's garbage collected
        process_and_save(batch)
```

**Pattern 2: Use generators**
```python
def process_stream(source):
    """Generator that processes rows without storing all in memory"""
    for row in source:
        yield transform(row)

with open_iterable('input.csv') as source:
    with open_iterable('output.jsonl', mode='w') as dest:
        dest.write_bulk(list(process_stream(source)))  # Process as generator
```

**Pattern 3: Avoid loading entire file**
```python
# ❌ Avoid: Loading entire file into memory
all_rows = list(open_iterable('large.csv'))  # Loads everything!

# ✅ Better: Process incrementally
with open_iterable('large.csv') as source:
    for row in source:
        process(row)
```

## Format Selection

### Performance Characteristics

Choose formats based on your performance requirements:

| Format | Read Speed | Write Speed | Memory | Compression | Best For |
|--------|-----------|-------------|--------|-------------|----------|
| CSV | Fast | Fast | Low | External | General purpose, compatibility |
| JSONL | Fast | Fast | Low | External | Streaming, APIs |
| Parquet | Very Fast | Fast | Medium | Built-in | Analytics, columnar queries |
| JSON | Slow* | N/A | High | External | Small files, nested data |
| Excel | Slow | Slow | High | External | Office integration |
| Arrow | Very Fast | Very Fast | Medium | Built-in | In-memory analytics |

\* JSON uses streaming parser for large files, improving performance.

### When to Use Each Format

**CSV:**
- ✅ Fast read/write
- ✅ Low memory usage
- ✅ Universal compatibility
- ❌ No nested data
- ❌ No type preservation

**JSONL:**
- ✅ Streaming support
- ✅ Nested data support
- ✅ Fast read/write
- ❌ No schema validation

**Parquet:**
- ✅ Columnar storage (fast queries)
- ✅ Built-in compression
- ✅ Schema preservation
- ❌ Requires PyArrow
- ❌ Less universal

**Arrow:**
- ✅ Fastest performance
- ✅ Zero-copy reads
- ✅ Columnar format
- ❌ Requires PyArrow
- ❌ Less common format

## Compression

### Compression Codecs

Different compression codecs offer different trade-offs:

| Codec | Speed | Ratio | CPU Usage | Best For |
|-------|-------|-------|-----------|----------|
| GZip | Medium | Good | Medium | General purpose |
| ZStandard | Fast | Excellent | Low | Production (recommended) |
| LZ4 | Very Fast | Fair | Very Low | Real-time processing |
| BZip2 | Slow | Excellent | High | Archival |
| Brotli | Slow | Excellent | High | Web delivery |

### Compression Impact

**Reading compressed files:**
- **GZip**: ~2-5x slower than uncompressed
- **ZStandard**: ~1.5-3x slower than uncompressed
- **LZ4**: ~1.2-2x slower than uncompressed

**Storage savings:**
- **CSV**: 70-90% size reduction
- **JSONL**: 70-90% size reduction
- **Parquet**: Already compressed (additional compression: 10-30%)

```python
# ✅ Compressed files save storage and I/O
with open_iterable('data.csv.zst') as source:  # ZStandard compression
    for row in source:
        process(row)
```

### When to Use Compression

**Use compression when:**
- ✅ File size >10MB
- ✅ Network I/O is bottleneck
- ✅ Storage costs matter
- ✅ Files are read multiple times

**Avoid compression when:**
- ❌ Real-time processing (under 100ms latency)
- ❌ CPU is bottleneck
- ❌ Files are written once, read never
- ❌ Very small files (under 1MB)

## Streaming vs Batch Processing

### Streaming (Iterator Pattern)

**Use streaming for:**
- Large files (>100MB)
- Memory-constrained environments
- Real-time processing
- Network streams

```python
# Streaming: Process one row at a time
with open_iterable('large.csv') as source:
    for row in source:  # Constant memory
        process(row)
```

**Advantages:**
- Constant memory usage
- Can start processing immediately
- Works with any file size

**Disadvantages:**
- Cannot seek/random access
- Slower for small files (overhead)

### Batch Processing

**Use batch processing for:**
- Medium files (1MB-100MB)
- When you need all data
- When processing benefits from batches

```python
# Batch: Process in chunks
with open_iterable('medium.csv') as source:
    while True:
        batch = source.read_bulk(10000)
        if not batch:
            break
        process_batch(batch)  # Process entire batch
```

**Advantages:**
- Better CPU cache utilization
- Can optimize batch operations
- Faster for medium files

**Disadvantages:**
- Higher memory usage
- Must wait for batch to fill

## DuckDB Engine

### When to Use DuckDB Engine

The DuckDB engine provides **significant performance improvements** for certain operations:

**Use DuckDB engine for:**
- ✅ Large CSV/JSONL files (>10MB)
- ✅ Fast row counting (`totals()`)
- ✅ Filtering and querying
- ✅ Aggregations

**Avoid DuckDB engine for:**
- ❌ Small files (under 1MB) - overhead not worth it
- ❌ Binary formats (Parquet, Arrow) - already optimized
- ❌ Real-time streaming - adds latency

```python
# ✅ DuckDB engine for fast operations
with open_iterable('large.csv.gz', engine='duckdb') as source:
    total = source.totals()  # Very fast row counting
    for row in source:
        process(row)
```

### Performance Comparison

| Operation | Standard Engine | DuckDB Engine | Speedup |
|-----------|----------------|---------------|---------|
| Row counting | O(n) scan | O(1) metadata | 100-1000x |
| Large CSV read | Sequential | Parallel | 2-5x |
| Filtering | Python loop | SQL filter | 5-10x |
| Aggregations | Python | SQL | 10-100x |

## Benchmarking

## Columnar tuning notes

Parquet `batch_size` controls read memory; `row_group_size` controls physical
write groups and is independent. Use a row-group target around 8K–64K rows for
general ETL, then tune against schema width and downstream scans. Arrow and
Lance flush bounded batches, while Vortex intentionally buffers a whole output
because its current writer replaces the store on each write.

`convert(..., use_native_batch=True, selection=BatchSelection(...))` enables
the Parquet/Arrow batch path with projection and row-range selection. Requests
that require flattening, validation hooks, or unsupported predicates fall back
to the row/bulk path unless `strict_native=True`.

Progress totals are evaluated once and do not consume seekable or codec-wrapped
inputs. Prefer the codec `balanced` profile for general workloads; choose
`fast` for CPU-bound pipelines and `max` for archival output.

### Measuring Performance

Use the built-in benchmarking tools:

```python
import time
from iterable.helpers.detect import open_iterable

# Measure read performance
start = time.perf_counter()
with open_iterable('data.csv') as source:
    count = 0
    for row in source:
        count += 1
elapsed = time.perf_counter() - start
print(f"Read {count} rows in {elapsed:.2f}s ({count/elapsed:.0f} rows/s)")
```

### Performance Testing

Run performance regression tests:

```bash
# Run benchmarks
pytest tests/test_benchmarks.py --benchmark-only

# Compare with baselines
pytest tests/test_performance_regression.py --benchmark-compare

# Update baselines after improvements
pytest tests/test_performance_regression.py --update-baselines
```

### Performance Profiling

Profile memory usage:

```python
from memory_profiler import profile

@profile
def process_file(filename):
    with open_iterable(filename) as source:
        for row in source:
            process(row)

process_file('large.csv')
```

## Best Practices Summary

### ✅ Do

1. **Use bulk operations** (`read_bulk()`, `write_bulk()`) for better performance
2. **Choose streaming formats** (CSV, JSONL) for large files
3. **Use appropriate batch sizes** (10,000-50,000 for most cases)
4. **Enable DuckDB engine** for large CSV/JSONL files
5. **Use compression** for files >10MB
6. **Process incrementally** - avoid loading entire files
7. **Use context managers** for automatic resource cleanup

### ❌ Don't

1. **Don't use individual operations** (`read()`, `write()`) for large datasets
2. **Don't load entire files** into memory unnecessarily
3. **Don't use non-streaming formats** (Excel, JSON) for large files
4. **Don't use tiny batch sizes** (under 100) - overhead dominates
5. **Don't skip compression** for large files
6. **Don't forget to close files** - use context managers

## Performance Checklist

Before deploying to production:

- [ ] Using bulk operations (`read_bulk()`, `write_bulk()`)
- [ ] Appropriate batch sizes (10K-50K)
- [ ] Streaming formats for large files
- [ ] Compression enabled for files >10MB
- [ ] DuckDB engine enabled for large CSV/JSONL
- [ ] Memory profiling completed
- [ ] Performance benchmarks run
- [ ] No memory leaks detected

## Related Topics

- [Best Practices](best-practices.md) - General best practices
- [Format Documentation](/formats/) - Format-specific performance notes
- [Troubleshooting](troubleshooting.md) - Performance troubleshooting
- [API Reference](/api/open-iterable) - Detailed API documentation
