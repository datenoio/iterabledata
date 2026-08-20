---
sidebar_position: 2
title: Data Pipelines
description: Build data processing pipelines with Iterable Data
---

# Data Pipelines

Iterable Data provides a powerful pipeline framework for processing data with transformation, progress tracking, and error handling.

## Basic Pipeline

A simple pipeline that transforms data:

```python
from iterable import open_iterable
from iterable.pipeline import pipeline

# Recommended: Using context managers
with open_iterable('input.parquet') as source:
    with open_iterable('output.jsonl.xz', mode='w') as destination:
        def transform_record(record, state):
            """Transform each record"""
            # Add processing logic
            out = {}
            for key in ['name', 'email', 'age']:
                if key in record:
                    out[key] = record[key]
            return out
        
        pipeline(
            source=source,
            destination=destination,
            process_func=transform_record
        )
# Files automatically closed
```

## Pipeline with Progress Tracking

Track progress during processing:

```python
from iterable import open_iterable
from iterable.pipeline import pipeline

# Recommended: Using context managers
with open_iterable('input.parquet') as source:
    with open_iterable('output.jsonl.xz', mode='w') as destination:
        def transform_record(record, state):
            """Transform each record"""
            return {'id': record.get('id'), 'value': record.get('value')}
        
        def progress_callback(stats, state):
            """Called every trigger_on records"""
            print(f"Processed {stats['rec_count']} records, "
                  f"Duration: {stats.get('duration', 0):.2f}s")
        
        def final_callback(stats, state):
            """Called when processing completes"""
            print(f"Total records: {stats['rec_count']}")
            print(f"Total time: {stats['duration']:.2f}s")
        
        pipeline(
            source=source,
            destination=destination,
            process_func=transform_record,
            trigger_func=progress_callback,
            trigger_on=1000,
            final_func=final_callback,
            start_state={}
        )
# Files automatically closed
```

## Pipeline with State

Use state to accumulate information during processing:

```python
from iterable import open_iterable
from iterable.pipeline import pipeline

source = open_iterable('input.jsonl')
with open_iterable('output.jsonl', mode='w') as destination:

    def transform_record(record, state):
        """Transform with state tracking"""
        state['count'] = state.get('count', 0) + 1
        record['sequence'] = state['count']
        return record

    def final_callback(stats, state):
        """Report final statistics"""
        print(f"Processed {state['count']} records")

    pipeline(
        source=source,
        destination=destination,
        process_func=transform_record,
        final_func=final_callback,
        start_state={'count': 0}
    )

    source.close()
```

## Filtering Records

Filter records by returning `None`:

```python
from iterable import open_iterable
from iterable.pipeline import pipeline

source = open_iterable('input.csv')
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
        skip_nulls=True  # Skip None values
    )

    source.close()
```

## Data Enrichment

Enrich records with additional data:

```python
from iterable import open_iterable
from iterable.pipeline import pipeline

source = open_iterable('input.jsonl')
with open_iterable('output.jsonl', mode='w') as destination:

    # Load lookup data
    lookup_table = load_lookup_data()

    def enrich_record(record, state):
        """Enrich record with lookup data"""
        key = record.get('id')
        if key in lookup_table:
            record['enriched_data'] = lookup_table[key]
        return record

    pipeline(
        source=source,
        destination=destination,
        process_func=enrich_record
    )

    source.close()
```

## Error Handling

Handle errors gracefully:

```python
from iterable import open_iterable
from iterable.pipeline import pipeline

source = open_iterable('input.jsonl')
with open_iterable('output.jsonl', mode='w') as destination:

    def transform_with_error_handling(record, state):
        """Transform with error handling"""
        try:
            # Process record
            result = process_record(record)
            return result
        except Exception as e:
            state['errors'] = state.get('errors', [])
            state['errors'].append(str(e))
            return None  # Skip this record

    def final_callback(stats, state):
        """Report errors"""
        if 'errors' in state:
            print(f"Encountered {len(state['errors'])} errors")

    pipeline(
        source=source,
        destination=destination,
        process_func=transform_with_error_handling,
        final_func=final_callback,
        start_state={}
    )

    source.close()
```

## Pipeline Parameters

The `pipeline()` function accepts these parameters:

- `source`: Input iterable object
- `destination`: Output iterable object (optional)
- `process_func`: Function to transform each record
- `trigger_func`: Function called periodically for progress
- `trigger_on`: Number of records between trigger calls
- `final_func`: Function called when processing completes
- `start_state`: Initial state dictionary
- `skip_nulls`: Skip None values (default: True)
- `reset_iterables`: Reset iterables before processing (default: True)

## Best Practices

1. **Use context managers**: Prefer `with` statements for automatic file cleanup
2. **Use progress callbacks**: Monitor long-running pipelines
3. **Handle errors**: Always include error handling in transformation functions
4. **Use state wisely**: Accumulate statistics or lookup data in state
5. **Filter early**: Return None to skip records you don't need
6. **Enable debug mode**: Use `debug=True` during development to catch errors early

## Related Topics

- [Format Conversion](/use-cases/format-conversion) - Convert between formats
- [API Reference: pipeline()](/api/pipeline) - Full API documentation
