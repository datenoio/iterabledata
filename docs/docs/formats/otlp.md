# OpenTelemetry Protocol (OTLP)

IterableData reads and writes OpenTelemetry export payloads as row envelopes with `signal`, `resource`, `scope`, and `record` fields. Two profiles exist:

- **`otlp-json`** — JSON documents (or JSON text) with `resourceSpans` / `resourceLogs` / `resourceMetrics`
- **`otlp-protobuf`** — binary ExportRequest protobuf; requires an explicit generated `message_class`

Unknown or malformed payloads raise a format error. No network calls or schema downloads occur.

## File Extensions

- `.json` / `.otlp.json` — OTLP JSON (`otlp-json`)
- Binary protobuf ExportRequest files — use `format="otlp-protobuf"` plus `message_class`

## Implementation Details

### Reading (JSON)

- Parses a single JSON object bounded by `max_message_bytes` (default 64 MiB)
- Expands traces, logs, and metrics into one row per span, log record, or metric data point
- Metric rows keep `metric`, `metric_type`, and `data_point` inside `record`

### Reading (Protobuf)

- Requires `message_class` (for example `ExportTraceServiceRequest`)
- Parses protobuf with official field-name preservation, then uses the same envelope layout as JSON

### Writing

- Groups rows back into resource/scope trees in a deterministic signal order (`traces`, `logs`, `metrics`)
- JSON writes a single object; protobuf serializes via `message_class`

## Usage

```python
from iterable import open_iterable

with open_iterable("export.json", iterableargs={"format": "otlp-json"}) as source:
    for row in source:
        print(row["signal"], row["record"])

# Protobuf needs a generated Export*ServiceRequest class
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest

with open_iterable(
    "export.bin",
    iterableargs={"format": "otlp-protobuf", "message_class": ExportTraceServiceRequest},
) as source:
    for row in source:
        print(row["signal"])
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `max_message_bytes` | int | `67108864` | No | Maximum encoded message size |
| `item_key` | str | none | No | JSON only: read a nested object at this key |
| `message_class` | protobuf class | none | **Yes for `otlp-protobuf`** | Generated ExportRequest type |

## Installation

```bash
pip install 'iterabledata[otlp]'
```

Protobuf profile also needs generated OpenTelemetry proto modules for `message_class`.

## Limitations

1. **Whole-message bound**: each file is one export payload up to `max_message_bytes`
2. **Protobuf needs `message_class`**
3. **No OTLP HTTP/gRPC client** — files and streams only

## Related Formats

- [JSON](json.md) / [JSON Lines](jsonl.md) — generic JSON
- [Protocol Buffers](protobuf.md) — generic protobuf messages
