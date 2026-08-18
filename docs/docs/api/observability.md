---
sidebar_position: 4
title: Observability
description: Progress tracking, metrics, and logging for conversions and pipelines
---

# Observability

IterableData provides comprehensive observability features for monitoring progress and performance of data conversions and pipelines. This includes progress callbacks, built-in progress bars, and standardized metrics objects.

## Overview

Observability features enable you to:
- Track progress in real-time during long-running operations
- Access structured metrics for programmatic workflows
- Integrate with monitoring systems and CI/CD pipelines
- Monitor performance and throughput

## Progress Callbacks

Progress callbacks allow you to receive real-time updates during conversion or pipeline execution.

### Conversion Progress Callbacks

```python
from iterable.convert import convert

def progress_callback(stats):
    """Called periodically during conversion"""
    print(f"Rows read: {stats['rows_read']}, "
          f"Rows written: {stats['rows_written']}, "
          f"Elapsed: {stats['elapsed']:.2f}s")
    
    if stats['estimated_total']:
        percent = (stats['rows_read'] / stats['estimated_total']) * 100
        print(f"Progress: {percent:.1f}%")

result = convert(
    'input.csv',
    'output.parquet',
    progress=progress_callback,
    progress_interval=500  # Call callback every 500 rows (default: 1000)
)
```

The progress callback receives a dictionary with:
- `rows_read`: Number of rows read from source
- `rows_written`: Number of rows written to destination
- `elapsed`: Elapsed time in seconds
- `estimated_total`: Estimated total rows (if available, otherwise `None`)
- `bytes_read`: Number of bytes read (if available, otherwise `None`)
- `bytes_written`: Number of bytes written (if available, otherwise `None`)
- `percent_complete`: Percentage complete (0-100) if `estimated_total` is available
- `estimated_time_remaining`: Estimated time remaining in seconds (if calculable, otherwise `None`)

### Pipeline Progress Callbacks

```python
from iterable import open_iterable
from iterable.pipeline import pipeline

def progress_callback(stats):
    """Called periodically during pipeline execution"""
    print(f"Rows processed: {stats['rows_processed']}, "
          f"Elapsed: {stats['elapsed']:.2f}s")
    
    if stats.get('throughput'):
        print(f"Throughput: {stats['throughput']:.0f} rows/second")

with open_iterable('input.csv') as source:
    with open_iterable('output.jsonl', mode='w') as destination:
        def process_func(record, state):
            return record
        
        result = pipeline(
            source=source,
            destination=destination,
            process_func=process_func,
            progress=progress_callback
        )
```

The progress callback receives a dictionary with:
- `rows_processed`: Number of rows processed
- `elapsed`: Elapsed time in seconds
- `throughput`: Rows per second (if calculable)
- `rec_count`: Total record count
- `exceptions`: Number of exceptions encountered
- `nulls`: Number of null results

## Built-in Progress Bars

The `convert()` function supports built-in progress bars using `tqdm` when available.

```python
from iterable.convert import convert

# Show progress bar during conversion
result = convert(
    'input.jsonl.gz',
    'output.parquet',
    show_progress=True
)
```

The progress bar:
- Shows rows processed and estimated time remaining
- Works automatically with `tqdm` if installed
- Gracefully falls back if `tqdm` is not available (no error)
- Respects the `silent` parameter (no progress bar if `silent=True`)

## Conversion Metrics

The `convert()` function returns a `ConversionResult` object with structured metrics.

### ConversionResult

```python
from iterable.convert import convert
from iterable.types import ConversionResult

result: ConversionResult = convert('input.csv', 'output.jsonl')

# Access metrics
print(f"Rows in: {result.rows_in}")
print(f"Rows out: {result.rows_out}")
print(f"Elapsed: {result.elapsed_seconds:.2f}s")
print(f"Bytes read: {result.bytes_read}")
print(f"Bytes written: {result.bytes_written}")

# Check for errors
if result.errors:
    print(f"Encountered {len(result.errors)} errors")
    for error in result.errors:
        print(f"  - {error}")
```

### ConversionResult Attributes

- `rows_in` (int): Total number of rows read from source
- `rows_out` (int): Total number of rows written to destination
- `elapsed_seconds` (float): Total elapsed time in seconds
- `bytes_read` (int | None): Number of bytes read (if available)
- `bytes_written` (int | None): Number of bytes written (if available)
- `errors` (list[Exception]): List of errors encountered (empty if none)

## Pipeline Metrics

The `pipeline()` function returns a `PipelineResult` object with structured metrics.

### PipelineResult

```python
from iterable import open_iterable
from iterable.pipeline import pipeline
from iterable.types import PipelineResult

with open_iterable('input.csv') as source:
    with open_iterable('output.jsonl', mode='w') as destination:
        def process_func(record, state):
            return record
        
        result: PipelineResult = pipeline(
            source=source,
            destination=destination,
            process_func=process_func
        )
        
        # Access metrics using attributes
        print(f"Rows processed: {result.rows_processed}")
        print(f"Elapsed: {result.elapsed_seconds:.2f}s")
        print(f"Throughput: {result.throughput:.0f} rows/second")
        print(f"Exceptions: {result.exceptions}")
        
        # Or use dictionary-style access (backward compatible)
        print(f"Record count: {result['rec_count']}")
        print(f"Duration: {result['duration']:.2f}s")
```

### PipelineResult Attributes

- `rows_processed` (int): Total number of rows processed
- `elapsed_seconds` (float): Total elapsed time in seconds
- `exceptions` (int): Number of exceptions encountered
- `nulls` (int): Number of null results
- `rec_count` (int): Total record count (alias for rows_processed)
- `time_start` (float | None): Start time timestamp
- `time_end` (float | None): End time timestamp
- `duration` (float | None): Duration in seconds (alias for elapsed_seconds)
- `throughput` (float | None): Rows per second (property, calculated)

### Backward Compatibility

`PipelineResult` supports both attribute access and dictionary-style access for backward compatibility:

```python
result = pipeline(...)

# New style (attribute access)
rows = result.rows_processed

# Old style (dictionary access) - still works
rows = result["rec_count"]
```

## Integration Examples

### CI/CD Integration

```python
from iterable.convert import convert

result = convert('input.csv', 'output.parquet')

# Log metrics for CI/CD
print(f"::set-output name=rows_in::{result.rows_in}")
print(f"::set-output name=rows_out::{result.rows_out}")
print(f"::set-output name=elapsed::{result.elapsed_seconds}")

# Fail build if errors occurred
if result.errors:
    raise Exception(f"Conversion failed with {len(result.errors)} errors")
```

### Monitoring Integration

```python
from iterable.convert import convert
import time

def send_metrics(stats):
    """Send metrics to monitoring system"""
    # Example: Send to Prometheus, Datadog, etc.
    metrics.gauge('conversion.rows_read', stats['rows_read'])
    metrics.gauge('conversion.rows_written', stats['rows_written'])
    metrics.gauge('conversion.elapsed', stats['elapsed'])

result = convert(
    'input.jsonl',
    'output.parquet',
    progress=send_metrics
)

# Send final metrics
metrics.gauge('conversion.total_rows', result.rows_out)
metrics.gauge('conversion.total_time', result.elapsed_seconds)
```

### Custom Progress Reporting

```python
from iterable.convert import convert
from datetime import datetime

class ProgressReporter:
    def __init__(self):
        self.start_time = datetime.now()
        self.updates = []
    
    def __call__(self, stats):
        """Progress callback"""
        update = {
            'timestamp': datetime.now(),
            'rows_read': stats['rows_read'],
            'rows_written': stats['rows_written'],
            'elapsed': stats['elapsed']
        }
        self.updates.append(update)
        
        # Print formatted progress
        elapsed_str = f"{stats['elapsed']:.1f}s"
        print(f"[{elapsed_str}] {stats['rows_read']} read, "
              f"{stats['rows_written']} written")

reporter = ProgressReporter()
result = convert('input.csv', 'output.jsonl', progress=reporter)

# Analyze progress updates
print(f"Total updates: {len(reporter.updates)}")
print(f"Average rows per second: "
      f"{result.rows_out / result.elapsed_seconds:.0f}")
```

## Configurable Progress Interval

By default, progress callbacks are invoked every 1000 rows. You can customize this interval using the `progress_interval` parameter:

```python
from iterable.convert import convert

def progress_callback(stats):
    print(f"Processed {stats['rows_read']} rows")

# Call callback every 500 rows for more frequent updates
result = convert(
    'input.csv',
    'output.parquet',
    progress=progress_callback,
    progress_interval=500
)

# Call callback every 5000 rows for less frequent updates (reduce overhead)
result = convert(
    'large_file.csv',
    'output.parquet',
    progress=progress_callback,
    progress_interval=5000
)
```

The `progress_interval` parameter is available in:
- `convert()` - Controls callback frequency during conversion
- `pipeline()` - Controls callback frequency during pipeline execution
- `bulk_convert()` - Passed to each file conversion

**Benefits**:
- Fine-grained control for fast operations (smaller intervals)
- Reduced overhead for very slow operations (larger intervals)
- Better performance tuning based on your use case

## Progress Tracking for Direct Iteration

For direct iteration over iterables (not using `convert()` or `pipeline()`), use the `with_progress()` helper function:

```python
from iterable import open_iterable
from iterable.helpers.progress import with_progress

def progress_callback(stats):
    print(f"Processed {stats['rows_read']} rows in {stats['elapsed']:.2f}s")
    if stats.get('throughput'):
        print(f"Throughput: {stats['throughput']:.0f} rows/second")

with open_iterable('large_file.csv') as source:
    for row in with_progress(source, callback=progress_callback, interval=1000):
        # Process each row
        process(row)
```

The `with_progress()` helper:
- Wraps any iterable with progress tracking
- Provides stats: `rows_read`, `elapsed`, `throughput`
- Configurable interval (default: 1000 rows)
- Handles callback errors gracefully (won't break iteration)

**Use cases**:
- Processing large files row-by-row
- Custom data transformations
- Filtering or validation operations
- Any scenario where you need progress tracking outside of `convert()` or `pipeline()`

## Error Handling in Callbacks

Progress callbacks are designed to be non-blocking. If a callback raises an exception, it's logged but doesn't stop the conversion or pipeline:

```python
def progress_callback(stats):
    # This error won't stop the conversion
    if stats['rows_read'] > 1000:
        raise ValueError("Test error")

result = convert('input.csv', 'output.jsonl', progress=progress_callback)
# Conversion continues even if callback raises an exception
```

## Structured Logging

IterableData provides structured logging capabilities with JSON and human-readable output formats, enabling better log analysis, filtering, and integration with log aggregation systems.

### Overview

Structured logging formats log entries as structured data (JSON) rather than plain text, making it easier to:
- Parse and analyze logs programmatically
- Filter logs by specific fields
- Integrate with log aggregation systems (ELK, Splunk, Datadog, etc.)
- Track operations with operation IDs and correlation IDs
- Query logs efficiently

### Configuration

#### Programmatic Configuration

```python
from iterable.helpers.structured_logging import configure_structured_logging
import logging

# Enable JSON structured logging
configure_structured_logging(
    format="json",
    level=logging.INFO
)

# Enable human-readable structured logging
configure_structured_logging(
    format="human",
    level=logging.DEBUG
)

# Write logs to file
configure_structured_logging(
    format="json",
    level=logging.INFO,
    output="iterabledata.log"
)
```

#### Environment Variable Configuration

You can enable structured logging via environment variables:

```bash
# Enable structured logging (JSON format)
export ITERABLEDATA_STRUCTURED_LOGGING=1

# Or specify format explicitly
export ITERABLEDATA_STRUCTURED_LOGGING=1
export ITERABLEDATA_LOG_FORMAT=json  # or "human"
```

**Environment Variables:**
- `ITERABLEDATA_STRUCTURED_LOGGING`: Set to `1`, `true`, or `yes` to enable
- `ITERABLEDATA_LOG_FORMAT`: `json` (default) or `human`

### Log Formats

#### JSON Format

JSON format produces machine-readable logs suitable for log aggregation systems:

```json
{
  "timestamp": "2026-01-28T10:30:45.123456+00:00",
  "level": "INFO",
  "logger": "iterable.detect",
  "message": "Detected format: csv",
  "module": "detect",
  "function": "detect_file_type",
  "line": 245,
  "operation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "correlation_id": "corr-12345",
  "format_id": "csv",
  "confidence": 1.0,
  "detection_method": "filename"
}
```

#### Human-Readable Format

Human-readable format produces developer-friendly logs:

```
[INFO] iterable.detect detect_file_type:245 op_id=a1b2c3d4 - Detected format: csv (format_id=csv, confidence=1.0, detection_method=filename)
```

### Operation Tracking

Structured logging supports operation tracking with operation IDs and correlation IDs:

```python
from iterable.helpers.structured_logging import OperationContext

# Track a conversion operation
with OperationContext("conversion", source_file="input.csv", dest_file="output.parquet"):
    convert('input.csv', 'output.parquet')
    # All logs within this context include the operation_id
```

**Operation Context Benefits:**
- **Operation IDs**: Unique identifier for each operation (UUID)
- **Correlation IDs**: Link related operations together
- **Context propagation**: Automatically included in all log entries
- **Traceability**: Track operations across multiple log entries

### Log Event Types

Structured logging uses standard event types for categorization:

- `format_detection`: Format detection operations
- `file_io`: File I/O operations
- `parsing`: Data parsing operations
- `conversion`: Format conversion operations
- `pipeline`: Pipeline processing operations
- `error`: Error events
- `performance`: Performance metrics
- `validation`: Data validation operations

### Integration Examples

#### ELK Stack (Elasticsearch, Logstash, Kibana)

```python
from iterable.helpers.structured_logging import configure_structured_logging
import logging

# Configure JSON logging for ELK
configure_structured_logging(
    format="json",
    level=logging.INFO,
    output="/var/log/iterabledata/iterabledata.log"
)

# Logstash can parse JSON logs directly
# Elasticsearch indexes structured fields for easy querying
```

#### Datadog Integration

```python
import logging
from iterable.helpers.structured_logging import configure_structured_logging

# Configure structured logging
configure_structured_logging(format="json", level=logging.INFO)

# Datadog agent automatically parses JSON logs
# Fields are available as tags/facets in Datadog
```

#### Custom Log Handler

```python
import logging
from iterable.helpers.structured_logging import configure_structured_logging, StructuredJSONFormatter

# Create custom handler (e.g., send to API)
class APIHandler(logging.Handler):
    def emit(self, record):
        log_data = self.format(record)
        # Send to your API
        send_to_api(json.loads(log_data))

# Configure with custom handler
handler = APIHandler()
handler.setFormatter(StructuredJSONFormatter())
configure_structured_logging(handler=handler, level=logging.INFO)
```

### Checking Logging Status

```python
from iterable.helpers.structured_logging import is_structured_logging_enabled

if is_structured_logging_enabled():
    print("Structured logging is enabled")
else:
    print("Structured logging is disabled")
```

### Best Practices

1. **Use JSON format for production**: JSON format is better for log aggregation systems
2. **Use human-readable for development**: Human-readable format is easier to read during development
3. **Set appropriate log levels**: Use `DEBUG` for development, `INFO` for production
4. **Use operation context**: Wrap operations in `OperationContext` for better traceability
5. **Integrate with monitoring**: Send structured logs to your monitoring/logging infrastructure

## Best Practices

1. **Use progress callbacks for long operations**: Progress callbacks are most useful for conversions or pipelines that take significant time
2. **Keep callbacks lightweight**: Avoid heavy operations in progress callbacks to maintain performance
3. **Handle errors gracefully**: Progress callbacks should handle errors internally to avoid disrupting the main operation
4. **Use metrics for automation**: Access `ConversionResult` and `PipelineResult` metrics programmatically for CI/CD and monitoring
5. **Combine with logging**: Use progress callbacks alongside structured logging for comprehensive observability
6. **Enable structured logging**: Use structured logging for better log analysis and integration with monitoring systems

## Related Topics

- [convert()](/api/convert) - Conversion function with progress support
- [pipeline()](/api/pipeline) - Pipeline function with progress support
- [Format Conversion Use Case](/use-cases/format-conversion)
- [Data Pipelines Use Case](/use-cases/data-pipelines)
