---
sidebar_position: 3
title: pipeline()
description: Build data processing pipelines with transformation and progress tracking
---

# pipeline()

The `pipeline()` function provides a framework for processing data with transformation functions, progress tracking, and state management.

## Signature

```python
pipeline(
    source: BaseIterable,
    destination: BaseIterable = None,
    process_func: Callable[[dict, dict], dict] = None,
    trigger_func: Callable[[dict, dict], None] = None,
    trigger_on: int = 1000,
    final_func: Callable[[dict, dict], None] = None,
    reset_iterables: bool = True,
    skip_nulls: bool = True,
    start_state: dict = {},
    debug: bool = False,
    batch_size: int = 1000,
    progress: Callable[[dict], None] = None,
    atomic: bool = False
) -> PipelineResult
```

## Parameters

### `source` (BaseIterable, required)

Input iterable object (from `open_iterable()`). Can be a file-based source or a database source (e.g., PostgreSQL, ClickHouse, MySQL, MongoDB).

### `destination` (BaseIterable, optional)

Output iterable object (from `open_iterable()`). If `None`, records are processed but not written.

### `process_func` (Callable, optional)

Function to transform each record. Signature:
```python
def process_func(record: dict, state: dict) -> dict:
    # Transform record
    return transformed_record  # or None to skip
```

### `trigger_func` (Callable, optional)

Function called periodically for progress tracking. Signature:
```python
def trigger_func(stats: dict, state: dict) -> None:
    # Report progress
    pass
```

### `trigger_on` (int, optional)

Number of records between `trigger_func` calls. Default: `1000`.

### `final_func` (Callable, optional)

Function called when processing completes. Signature:
```python
def final_func(stats: dict, state: dict) -> None:
    # Report final statistics
    pass
```

### `reset_iterables` (bool, optional)

If `True`, resets iterables before processing. Default: `True`.

### `skip_nulls` (bool, optional)

If `True`, skips records where `process_func` returns `None`. Default: `True`.

### `start_state` (dict, optional)

Initial state dictionary passed to all callback functions. Default: `{}`.

### `debug` (bool, optional)

Enable debug mode for additional logging. Default: `False`.

### `batch_size` (int, optional)

Number of records to batch before writing to destination. Default: `1000`.

### `progress` (Callable, optional)

Optional callback function that receives progress updates during pipeline execution. The callback receives a dictionary with:
- `rows_processed`: Number of rows processed
- `elapsed`: Elapsed time in seconds
- `throughput`: Rows per second (if calculable)
- `rec_count`: Total record count (same as rows_processed)
- `exceptions`: Number of exceptions encountered
- `nulls`: Number of null results

### `atomic` (bool, optional)

If `True` and destination is a file, writes to a temporary file and atomically renames it to the destination upon successful completion. This ensures output files are never left in a partially written state, which is important for production environments. If the pipeline fails or is interrupted, the original destination file (if it existed) remains unchanged and the temporary file is cleaned up.

**Note**: Atomic writes only work when destination is a file-based iterable and only on the same filesystem. If destination is a stream or in-memory object, atomic writes are skipped. Default: `False`.

The callback is invoked periodically during execution (every 1000 rows by default).

## Return Value

Returns a `PipelineResult` object containing pipeline execution metrics. The result supports both attribute access and dictionary-style access for backward compatibility:

- `rows_processed`: Total number of rows processed
- `elapsed_seconds`: Total elapsed time in seconds
- `exceptions`: Number of exceptions encountered
- `nulls`: Number of null results
- `rec_count`: Total record count (alias for rows_processed)
- `time_start`: Start time timestamp
- `time_end`: End time timestamp
- `duration`: Duration in seconds (alias for elapsed_seconds)
- `throughput`: Rows per second (property)

You can access metrics using either:
- Attribute access: `result.rows_processed`
- Dictionary access: `result["rec_count"]` (for backward compatibility)

## Statistics Dictionary

The `stats` dictionary passed to callbacks contains:
- `rec_count` - Number of records processed
- `nulls` - Number of null/skipped records
- `exceptions` - Number of exceptions encountered
- `time_start` - Processing start time
- `duration` - Processing duration (in final_func)

## Examples

### Basic Pipeline

```python
from iterable import open_iterable
from iterable.pipeline import pipeline

# Recommended: Using context managers
with open_iterable('input.parquet') as source:
    with open_iterable('output.jsonl.xz', mode='w') as destination:
        def transform_record(record, state):
            """Transform each record"""
            return {'id': record.get('id'), 'value': record.get('value')}
        
        pipeline(
            source=source,
            destination=destination,
            process_func=transform_record
        )
# Files automatically closed
```

### Pipeline with Progress Tracking

```python
from iterable import open_iterable
from iterable.pipeline import pipeline

# Recommended: Using context managers
with open_iterable('input.parquet') as source:
    with open_iterable('output.jsonl.xz', mode='w') as destination:
        def transform_record(record, state):
            return record
        
        def progress_callback(stats, state):
            print(f"Processed {stats['rec_count']} records")
        
        def final_callback(stats, state):
            print(f"Total: {stats['rec_count']} records")
            print(f"Duration: {stats['duration']:.2f}s")
        
        pipeline(
            source=source,
            destination=destination,
            process_func=transform_record,
            trigger_func=progress_callback,
            trigger_on=1000,
            final_func=final_callback
        )
# Files automatically closed
```

### Pipeline with Progress Callback

```python
from iterable import open_iterable
from iterable.pipeline import pipeline

def progress_callback(stats):
    print(f"Progress: {stats['rows_processed']} rows, "
          f"{stats['elapsed']:.2f}s, "
          f"{stats.get('throughput', 0):.0f} rows/sec")

with open_iterable('input.csv') as source:
    with open_iterable('output.jsonl', mode='w') as destination:
        def transform_record(record, state):
            return record
        
        result = pipeline(
            source=source,
            destination=destination,
            process_func=transform_record,
            progress=progress_callback
        )
        
        # Access metrics
        print(f"Processed {result.rows_processed} rows")
        print(f"Throughput: {result.throughput:.0f} rows/second")
# Files automatically closed
```

### Accessing Pipeline Metrics

```python
from iterable import open_iterable
from iterable.pipeline import pipeline

with open_iterable('input.jsonl') as source:
    with open_iterable('output.csv', mode='w') as destination:
        def transform_record(record, state):
            return record
        
        result = pipeline(
            source=source,
            destination=destination,
            process_func=transform_record
        )
        
        # Access metrics using attributes
        print(f"Rows processed: {result.rows_processed}")
        print(f"Time elapsed: {result.elapsed_seconds:.2f}s")
        print(f"Exceptions: {result.exceptions}")
        
        # Or use dictionary-style access (backward compatible)
        print(f"Record count: {result['rec_count']}")
        print(f"Duration: {result['duration']:.2f}s")
        
        # Calculate throughput
        if result.throughput:
            print(f"Throughput: {result.throughput:.0f} rows/second")
# Files automatically closed
```

### Pipeline with Database Source

```python
from iterable import open_iterable
from iterable.pipeline import pipeline

# Process data from PostgreSQL database
source = open_iterable(
    'postgresql://user:password@localhost:5432/mydb',
    engine='postgres',
    iterableargs={'query': 'users', 'filter': 'active = TRUE'}
)

with open_iterable('output.jsonl', mode='w') as destination:
    def transform_record(record, state):
        # Transform database row
        return {
            'id': record['id'],
            'name': record['name'],
            'email': record['email']
        }
    
    result = pipeline(
        source=source,
        destination=destination,
        process_func=transform_record,
        reset_iterables=False  # Database sources don't support reset
    )
    
    print(f"Processed {result.rows_processed} rows from database")
source.close()  # Close database connection

# Process data from ClickHouse database
source = open_iterable(
    'clickhouse://user:password@localhost:9000/analytics',
    engine='clickhouse',
    iterableargs={
        'query': 'events',
        'settings': {'max_threads': 4}
    }
)

with open_iterable('events_output.parquet', mode='w') as destination:
    def transform_record(record, state):
        # Transform ClickHouse row
        return {
            'id': record['id'],
            'event_type': record['event_type'],
            'timestamp': record['timestamp']
        }
    
    result = pipeline(
        source=source,
        destination=destination,
        process_func=transform_record,
        reset_iterables=False  # Database sources don't support reset
    )
    
    print(f"Processed {result.rows_processed} rows from ClickHouse")
source.close()  # Close database connection
```

### Pipeline with State

```python
from iterable import open_iterable
from iterable.pipeline import pipeline

# Recommended: Using context managers
with open_iterable('input.jsonl') as source:
    with open_iterable('output.jsonl', mode='w') as destination:
        def transform_with_state(record, state):
            state['count'] = state.get('count', 0) + 1
            record['sequence'] = state['count']
            return record
        
        def final_callback(stats, state):
            print(f"Processed {state['count']} records")
        
        pipeline(
            source=source,
            destination=destination,
            process_func=transform_with_state,
            final_func=final_callback,
            start_state={'count': 0}
        )
# Files automatically closed
```

### Filtering Records

```python
from iterable import open_iterable
from iterable.pipeline import pipeline

# Recommended: Using context managers
with open_iterable('input.csv') as source:
    with open_iterable('output.csv', mode='w') as destination:
        def filter_records(record, state):
            """Only process records that meet criteria"""
            if record.get('age', 0) >= 18:
                return record
            return None  # Skip this record
        
        pipeline(
            source=source,
            destination=destination,
            process_func=filter_records,
            skip_nulls=True
        )
# Files automatically closed
```

## Error Handling

```python
from iterable import open_iterable
from iterable.pipeline import pipeline

try:
    with open_iterable('input.csv') as source:
        with open_iterable('output.csv', mode='w') as destination:
            def transform_record(record, state):
                # Include error handling in transform function
                try:
                    # Your transformation logic
                    return transformed_record
                except Exception as e:
                    # Log error and skip record
                    state['errors'] = state.get('errors', 0) + 1
                    return None  # Skip this record
            
            pipeline(
                source=source,
                destination=destination,
                process_func=transform_record,
                debug=True  # Enable debug mode for more error details
            )
except Exception as e:
    print(f"Pipeline error: {e}")
```

### Common Errors

- **AttributeError**: Check that records have expected keys before accessing
- **TypeError**: Ensure `process_func` returns a dictionary or `None`
- **FileNotFoundError**: Verify input file exists and output directory is writable
- **MemoryError**: Process in smaller batches or reduce `trigger_on` frequency

## Troubleshooting

### Pipeline Runs Slowly

- **Check `process_func`**: Ensure transformation logic is efficient
- **Reduce `trigger_on` frequency**: Less frequent callbacks improve performance
- **Use bulk operations**: Consider using `write_bulk()` in destination if supported
- **Profile your code**: Identify bottlenecks in transformation logic

### Records Not Being Written

- **Check return value**: `process_func` must return a dictionary (not `None`) to write
- **Check `skip_nulls`**: If `True`, `None` returns are skipped
- **Check destination**: Verify destination file is opened in write mode
- **Check errors**: Enable `debug=True` to see exceptions

### State Not Persisting

- **State is per-pipeline**: State is reset for each pipeline run
- **Use `start_state`**: Initialize state with `start_state` parameter
- **State is mutable**: Modify state dictionary directly (it's passed by reference)

## Best Practices

1. **Use context managers**: Prefer `with` statements for automatic file cleanup
2. **Handle errors**: Include error handling in `process_func` to skip bad records
3. **Use state wisely**: Accumulate statistics or lookup data in state
4. **Monitor progress**: Use `trigger_func` for long-running pipelines
5. **Filter early**: Return `None` to skip records you don't need
6. **Enable debug mode**: Use `debug=True` during development to catch errors early

## Related Topics

- [Data Pipelines Use Case](/use-cases/data-pipelines)
- [open_iterable()](/api/open-iterable) - Opening files
- [Database Engines](/api/database-engines) - Database source support
- [BaseIterable Methods](/api/base-iterable)
