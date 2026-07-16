## 1. Model and registration

- [x] 1.1 Define the signal/resource/scope/record row envelope and exact type mappings.
- [x] 1.2 Add `otlp-json` and `otlp-protobuf` descriptors, aliases/extensions, maturity, memory behavior, and optional extras.
- [ ] 1.3 Add conservative OTLP JSON content detection and explicit binary profile selection.
- [x] 1.4 Add configurable JSON nesting/item and Protobuf message-size limits.

## 2. Reading

- [ ] 2.1 Implement incremental OTLP JSON trace and log iteration.
- [x] 2.2 Implement all supported OTLP metric/data-point variants with metric context.
- [x] 2.3 Implement Protobuf ExportRequest parsing with official message definitions.
- [x] 2.4 Preserve ids, bytes, enums, timestamps, attributes, events, links, exemplars, and 64-bit values.
- [x] 2.5 Implement `read()`, `read_bulk()`, reset, totals where cheap, and error-policy behavior.

## 3. Writing

- [x] 3.1 Group rows deterministically by signal, resource, and instrumentation scope.
- [x] 3.2 Implement OTLP JSON mapping writes for traces, logs, and metrics.
- [x] 3.3 Implement equivalent Protobuf ExportRequest writes.
- [ ] 3.4 Validate metric point/type compatibility and required identifiers.

## 4. Tests and documentation

- [ ] 4.1 Add official/conformant JSON and Protobuf fixtures for all three signals and metric variants.
- [ ] 4.2 Add JSON↔Protobuf logical equivalence and round-trip tests.
- [ ] 4.3 Add malformed, unknown-field, oversize, empty, missing-dependency, detection-collision, and memory tests.
- [x] 4.4 Document profiles, row schema, mappings, memory/security limits, and conversion examples.
- [ ] 4.5 Run representative observability/serialization CI and strict OpenSpec validation.
