# Change: Add OTLP JSON and Protobuf Format Profiles

## Why

IterableData already supports log/event formats, Protobuf, conversion, observability metrics, and agent tooling, but it cannot iterate OpenTelemetry Protocol exports directly. OTLP files contain nested resource and instrumentation-scope envelopes; a profile must yield individual spans, log records, and metric data points without losing context or violating OTLP JSON's integer/string rules.

## What Changes

- Add `otlp-json` and `otlp-protobuf` profiles for exported traces, logs, and metrics.
- Yield one span, log record, or metric data point per row with resource, scope, signal, and metric context.
- Stream recognized OTLP JSON envelopes where possible and explicitly declare Protobuf export-request memory behavior.
- Preserve trace/span identifiers, bytes, enums, timestamps, and 64-bit JSON values according to OTLP/Protobuf mappings.
- Support profile-aware writes, detection, optional dependencies, malformed/oversize protections, fixtures, and docs.

## Dependencies

- Coordinate descriptor/profile metadata with `unify-format-capability-metadata`.
- Reuse generic Protobuf and JSON parsing infrastructure without changing their default row models.

## Impact

- Affected specs: `otlp-formats`
- Affected code: new OTLP profiles/helpers, format registry/content detection, optional dependencies, tests/docs
- New dependency: optional OpenTelemetry Protobuf definitions/runtime for binary OTLP
- Non-goal: no collector, network exporter, or live OTLP transport is added
