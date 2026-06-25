---
sidebar_position: 21
title: Async/Await Support
description: Asynchronous I/O operations for concurrent processing
---

# Async/Await Support

IterableData provides async/await support for asynchronous I/O operations, enabling concurrent file processing and non-blocking operations.

## Overview

The async API mirrors the synchronous API but uses async/await patterns:

- **`aopen_iterable()`** - Async version of `open_iterable()`
- **`AsyncBaseIterable`** - Async base class for iterables
- **Async methods** - `aread()`, `aread_bulk()`, `awrite()`, `awrite_bulk()`

## Basic Usage

### Reading Files Asynchronously

```python
import asyncio
from iterable.helpers.async_detect import aopen_iterable

async def main():
    source = await aopen_iterable('data.csv')
    async with source:
        async for row in source:
            print(row)

asyncio.run(main())
```

### Bulk Reading

```python
async def main():
    source = await aopen_iterable('data.csv')
    async with source:
        batch = await source.aread_bulk(1000)
        for row in batch:
            process(row)

asyncio.run(main())
```

### Concurrent File Processing

One of the main benefits of async support is concurrent file processing:

```python
import asyncio
from iterable.helpers.async_detect import aopen_iterable

async def process_file(filename: str):
    source = await aopen_iterable(filename)
    async with source:
        rows = []
        async for row in source:
            rows.append(row)
        return rows

async def main():
    files = ['file1.csv', 'file2.csv', 'file3.csv']
    results = await asyncio.gather(*[process_file(f) for f in files])
    print(f"Processed {len(results)} files")

asyncio.run(main())
```

## API Reference

### `aopen_iterable()`

Async version of `open_iterable()`:

```python
async def aopen_iterable(
    filename: str,
    mode: str = "r",
    engine: str = "internal",
    iterableargs: dict[str, Any] | None = None,
    codecargs: dict[str, Any] | None = None,
    debug: bool = False,
) -> AsyncBaseIterable
```

**Parameters**:
- `filename`: Path to file or connection string
- `mode`: File mode ('r' for read, 'w' for write)
- `engine`: Processing engine ('internal', 'duckdb', or database engine)
- `iterableargs`: Format-specific arguments
- `codecargs`: Codec-specific arguments
- `debug`: Enable debug logging

**Returns**: `AsyncBaseIterable` instance

### AsyncBaseIterable

Base class for async iterables with the following methods:

- `async def aread(skip_empty: bool = True) -> Row` - Read single row
- `async def aread_bulk(num: int = 1000) -> list[Row]` - Read multiple rows
- `async def awrite(record: Row) -> None` - Write single row
- `async def awrite_bulk(records: list[Row]) -> None` - Write multiple rows
- `async def areset() -> None` - Reset iterator
- `async def aclose() -> None` - Close iterable

### Async Iterator Protocol

Async iterables support the async iterator protocol:

```python
async def main():
    source = await aopen_iterable('data.csv')
    async with source:
        # Using async for
        async for row in source:
            process(row)
        
        # Or manual iteration
        iterator = aiter(source)
        try:
            while True:
                row = await anext(iterator)
                process(row)
        except StopAsyncIteration:
            pass
```

## Implementation Details

### Phase 1: Foundation (Current)

The current implementation (Phase 1) uses a **wrapper approach**:

- Wraps synchronous `open_iterable()` and iterable classes
- Uses `asyncio.run_in_executor()` to run synchronous operations in thread pool
- Provides async interface while reusing existing synchronous implementations

**Benefits**:
- ✅ Minimal code changes
- ✅ Reuses all existing format implementations
- ✅ Easy to implement and maintain

**Limitations**:
- Uses thread pool (not true async I/O)
- Overhead of thread pool management
- Best for I/O-bound operations

### Future Phases

**Phase 2: Native Async I/O** (Planned)
- Native async I/O for network sources (S3, GCS, Azure)
- Native async database drivers
- True async operations without thread pool

**Phase 3: Advanced Features** (Planned)
- `apipeline()` - Async data pipelines
- `aconvert()` - Async format conversion
- Async progress callbacks

## When to Use Async

Async support is beneficial for:

✅ **Concurrent file processing** - Process multiple files simultaneously  
✅ **Network sources** - Reading from cloud storage or remote databases  
✅ **I/O-bound operations** - When waiting for I/O is the bottleneck  
✅ **Integration with async frameworks** - When using async web frameworks

Not beneficial for:

❌ **CPU-bound operations** - Async doesn't help with CPU-intensive tasks  
❌ **Single file processing** - Overhead may not be worth it  
❌ **Simple scripts** - Synchronous API is simpler for basic use cases

## Examples

### Example 1: Process Multiple Files Concurrently

```python
import asyncio
from iterable.helpers.async_detect import aopen_iterable

async def count_rows(filename: str) -> int:
    count = 0
    source = await aopen_iterable(filename)
    async with source:
        async for row in source:
            count += 1
    return count

async def main():
    files = ['data1.csv', 'data2.csv', 'data3.csv']
    counts = await asyncio.gather(*[count_rows(f) for f in files])
    total = sum(counts)
    print(f"Total rows: {total}")

asyncio.run(main())
```

### Example 2: Async Pipeline Processing

```python
async def process_with_api(row):
    # Simulate API call
    await asyncio.sleep(0.1)
    return {**row, 'enriched': True}

async def main():
    source = await aopen_iterable('input.csv')
    dest = await aopen_iterable('output.jsonl', mode='w')
    
    async with source, dest:
        async for row in source:
            enriched = await process_with_api(row)
            await dest.awrite(enriched)

asyncio.run(main())
```

## Backward Compatibility

The async API is **additive** - it doesn't change the synchronous API:

- ✅ Synchronous `open_iterable()` continues to work
- ✅ All existing code remains unchanged
- ✅ Async support is opt-in

## Related Topics

- [open_iterable()](/api/open-iterable) - Synchronous file opening
- [Base Classes](/api/base-iterable) - Base iterable classes
- [Database Engines](/api/database-engines) - Database sources (async support planned)
