# OpenTelemetry Protocol (OTLP)

IterableData reads and writes OpenTelemetry export payloads as row envelopes with `signal`, `resource`, `scope`, and `record` fields. Two profiles exist:

- **`otlp-json`** — JSON documents with `resourceSpans` / `resourceLogs` / `resourceMetrics`
- **`otlp-protobuf`** — binary ExportRequest protobuf; requires an explicit generated `message_class`

Unknown or malformed payloads raise a format error. No network calls or schema downloads occur.

## File Extensions

- `.otlp.json` — OTLP JSON (`otlp-json`); also detected from content when a document has a recognized top-level OTLP envelope key
- `.otlp.pb` / `.otlp.protobuf` — OTLP Protobuf (`otlp-protobuf`); binary payloads otherwise require explicit `format="otlp-protobuf"` plus `message_class`, because protobuf has no reliable magic signature

## Row Schema

Every row carries:

| Field | Content |
|-------|---------|
| `signal` | `"trace"`, `"log"`, or `"metric"` |
| `resource` | OTLP Resource envelope dict (may be empty) |
| `scope` | Instrumentation scope dict (may be empty) |
| `record` | One span, one log record, or one metric data point |

Metric rows additionally carry:

| Field | Content |
|-------|---------|
| `metric` | `{"name", "description", "unit"}` context of the owning metric |
| `metric_type` | `gauge`, `sum`, `histogram`, `exponentialHistogram`, or `summary` |
| `aggregation_temporality` | OTLP enum int (`1`=DELTA, `2`=CUMULATIVE); sum/histogram/exponentialHistogram only |
| `is_monotonic` | bool; sum only |

Type mapping notes:

- `traceId` / `spanId` / `parentSpanId` (including nested event links and exemplars) are lowercase hex strings in both profiles, per the OTLP JSON mapping. Protobuf reads convert wire bytes to hex; protobuf writes convert hex back to bytes.
- 64-bit integers (`startTimeUnixNano`, `asInt`, histogram counts, ...) remain exact JSON strings; they are never coerced through floating point.
- Enums are represented as integers (stable protobuf numbering) in both profiles.
- Other bytes fields (e.g. AnyValue `bytesValue`) use standard base64.
- Unknown JSON fields inside records are preserved and written back.

## Implementation Details

### Reading (JSON)

- Documents up to 256 KiB (and non-seekable streams) are parsed eagerly, so malformed input fails at open time.
- Larger seekable documents are parsed **incrementally** with the optional `ijson` dependency: one resource envelope is materialized at a time and individual spans, log records, and metric data points are yielded as rows without building all rows in memory. Without `ijson`, a bounded whole-document fallback is used.
- All paths enforce `max_message_bytes` (default 64 MiB).
- `totals()` is available; on streaming sources it performs a separate counting pass and rewinds the iterator.

### Reading (Protobuf)

- Requires `message_class` (for example `ExportTraceServiceRequest`).
- A standard ExportRequest is one protobuf message: parsing is a whole-message operation bounded by `max_message_bytes`, and the capability metadata declares `read_memory="whole_input"`.
- Parsed with the official message definitions, then exposed through the same row envelope as OTLP JSON.

### Writing

- Rows are buffered and written as a single document on `flush()`/`close()`, grouped deterministically by signal (`trace`, `log`, `metric` order), then resource, then scope. Metric data points merge per metric identity.
- Write-time validation rejects:
  - unknown `signal` values;
  - spans without valid `traceId` (32 hex chars) / `spanId` (16 hex chars), and malformed log correlation ids;
  - metrics without a non-empty `name`, with an unknown `metric_type`, with `sum` missing `aggregation_temporality`/`is_monotonic`, with temporality/monotonicity set on gauge/summary, or with a data-point payload that belongs to a different metric type (e.g. `quantileValues` on a gauge).
- JSON writes follow the OTLP JSON mapping; protobuf writes serialize through the official `message_class` descriptor.
- `otlp-protobuf` writes only the root field the message class declares (e.g. `ExportTraceServiceRequest` accepts only `resourceSpans`).

## Usage

```python
from iterable import open_iterable

with open_iterable("export.otlp.json") as source:          # detected from extension/content
    for row in source:
        print(row["signal"], row["record"])

with open_iterable("export.json", format="otlp-json") as source:   # explicit forcing
    ...

# Protobuf needs a generated Export*ServiceRequest class
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest

with open_iterable(
    "export.bin",
    format="otlp-protobuf",
    iterableargs={"message_class": ExportTraceServiceRequest},
) as source:
    for row in source:
        print(row["signal"])
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `max_message_bytes` | int | `67108864` | No | Maximum encoded message size (read and write) |
| `item_key` | str | none | No | JSON only: read the OTLP envelope nested at this key |
| `message_class` | protobuf class | none | **Yes for `otlp-protobuf`** | Generated ExportRequest type |

## Installation

```bash
pip install 'iterabledata[otlp]'   # protobuf + ijson
```

The protobuf profile also needs generated OpenTelemetry proto modules (for example `opentelemetry-proto`) for `message_class`.

## Limitations

1. **Message bound**: each file is one export payload up to `max_message_bytes`. JSON yields records incrementally for large documents; protobuf ExportRequest parsing is whole-message by design.
2. **Protobuf needs `message_class`** — binary OTLP cannot be sniffed reliably.
3. **No OTLP HTTP/gRPC client** — files and streams only.
4. **One document per file** — length-delimited protobuf streams are not guessed; concatenate exports as separate files or wrap them yourself.


## Error Handling

- **Missing dependency**: `otlp-protobuf` without `protobuf` raises `ImportError` naming `pip install 'iterabledata[otlp]'`.
- **Malformed input**: invalid JSON/protobuf raises `ValueError` with the underlying parser detail; oversize payloads raise `ValueError` naming the configured `max_message_bytes`.
- **Invalid rows on write**: metric/type mismatches and missing identifiers raise `ValueError`/`TypeError` before anything is written.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [JSON](json.md) / [JSON Lines](jsonl.md) — generic JSON
- [Protocol Buffers](protobuf.md) — generic protobuf messages
