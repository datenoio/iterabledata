# Apache Flink Format

## Description

Apache Flink is a stream processing framework. This implementation handles Flink checkpoint format for reading/writing Flink checkpoint data. Flink checkpoints contain checkpoint ID, timestamp, and state data.

## File Extensions

- `.ckpt` - Flink checkpoint files

## Implementation Details

### Reading

The Flink implementation:
- Parses Flink checkpoint format
- Extracts checkpoint ID, timestamp, and state data
- Handles binary checkpoint data
- Converts checkpoint records to dictionaries
- Supports metadata inclusion/exclusion

### Writing

Writing support:
- Writes a simplified checkpoint dump (not a live Flink job)
- Stores `checkpoint_id`, `timestamp`, and remaining fields as state JSON

### Key Features

- **Checkpoint format**: Handles Flink checkpoint structure
- **Metadata support**: Includes checkpoint ID and timestamp
- **State data**: Extracts Flink state data
- **Nested data**: Supports complex state structures

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('checkpoint.ckpt', iterableargs={
    'include_metadata': True
}) as source:
    for record in source:
        print(record)  # Contains checkpoint_id, timestamp, state_data

# Writing
with open_iterable('output.ckpt', mode='w') as dest:
    dest.write({'checkpoint_id': 1, 'timestamp': 0, 'state': {'n': 1}})
```

## Parameters

- `include_metadata` (bool): Include checkpoint_id, timestamp (default: `True`)

## Limitations

1. **Binary format**: Not human-readable
2. **Flink-specific**: Designed for Flink checkpoint format
3. **Format complexity**: Flink checkpoint format can be complex
4. **Simplified implementation**: May not support all Flink features

## Compression Support

Flink checkpoint files can be compressed with all supported codecs:
- GZip (`.ckpt.gz`)
- BZip2 (`.ckpt.bz2`)
- LZMA (`.ckpt.xz`)
- LZ4 (`.ckpt.lz4`)
- ZIP (`.ckpt.zip`)
- Brotli (`.ckpt.br`)
- ZStandard (`.ckpt.zst`)

## Use Cases

- **Stream processing**: Processing Flink checkpoint data
- **State recovery**: Recovering Flink application state
- **Checkpoint analysis**: Analyzing Flink checkpoints
- **Data migration**: Migrating Flink state data

## Related Formats

- [Kafka](kafka.md) - Apache Kafka format
- [Pulsar](pulsar.md) - Apache Pulsar format
