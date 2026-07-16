## Context

OTLP export requests group data by resource and instrumentation scope. Traces contain spans, logs contain log records, and metrics contain several data-point variants. JSON and Protobuf use related schemas but different physical representations and memory characteristics.

## Goals / Non-Goals

- Goals:
  - Iterate individual signal records with inherited context.
  - Preserve OTLP data types and identifier semantics across JSON/Protobuf profiles.
  - Provide bounded JSON parsing and explicit binary size limits.
  - Round-trip supported export requests.
- Non-Goals:
  - Send or receive OTLP over gRPC/HTTP.
  - Implement a telemetry backend or aggregation engine.
  - Flatten every attribute into top-level columns by default.

## Decisions

### Profile identity and detection

Canonical ids are `otlp-json` and `otlp-protobuf`. JSON content detection recognizes top-level `resourceSpans`, `resourceLogs`, or `resourceMetrics`; explicit format selection is always supported. Binary Protobuf generally requires explicit format or an unambiguous extension because it lacks a reliable universal magic signature.

### Row envelope

Each row contains `signal` (`trace`, `log`, or `metric`), normalized `resource`, `scope`, and `record`. Metric rows also carry metric name, description, unit, aggregation type, temporality/monotonicity where applicable, and one data point in `record`. A flatten option may be layered through existing conversion tools.

### Type fidelity

Trace/span ids and byte fields use documented hexadecimal/base64 representations. Protobuf enums use stable symbolic or integer mappings. OTLP JSON 64-bit integer strings remain lossless and are not coerced through floating point. Unknown fields are preserved where the backend supports them or reported according to strictness.

### Memory and framing

OTLP JSON uses incremental item parsing for recognized envelopes. A standard binary ExportRequest is one Protobuf message and may require whole-message parsing; configurable maximum message size is enforced and the descriptor declares this memory behavior. Optional length-delimited message streams may be supported explicitly, not guessed.

### Writes

Rows are grouped back into resource/scope envelopes. Writers preserve supplied grouping keys/order deterministically and validate that metric points match their metric type. JSON writes follow the OTLP JSON mapping; Protobuf writes use official message definitions.

## Risks / Trade-offs

- Metric variants make one flat schema unwieldy. Mitigation: stable envelope plus typed `record` payload.
- Binary messages can be large. Mitigation: explicit maximum size and truthful whole-message declaration.
- JSON detection can collide with ordinary JSON. Mitigation: require recognized top-level OTLP keys and allow explicit override.

## Migration Plan

Implement JSON traces/logs first, then JSON metrics, binary Protobuf parity, and finally writes. Keep profiles experimental until cross-encoding equivalence fixtures pass.

## Open Questions

- Should unknown Protobuf fields be retained as serialized bytes for lossless rewrite?
- Which extension(s), if any, are sufficiently unambiguous for automatic OTLP Protobuf detection?
