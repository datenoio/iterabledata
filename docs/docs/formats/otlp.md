# OpenTelemetry Protocol

`OTLPJSONIterable` exposes traces, logs, and metrics as envelopes with
`signal`, `resource`, `scope`, and `record` fields. Metrics retain metric type
and data-point context. `OTLPProtobufIterable` accepts an explicit generated
ExportRequest `message_class`, preserving protobuf enum/bytes/64-bit parsing
and enforcing `max_message_bytes`.

Signal-specific grouping is deterministic on writes. Unknown or malformed
payloads fail with a format error; no network calls or automatic schema
downloads occur.
