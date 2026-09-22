## ADDED Requirements

### Requirement: OTLP JSON Profile Reading

The system SHALL recognize OTLP JSON export envelopes for traces, logs, and metrics and SHALL yield one logical span, log record, or metric data point per row with resource and instrumentation-scope context.

#### Scenario: Read trace export

- **WHEN** OTLP JSON contains `resourceSpans`
- **THEN** each span SHALL yield one row with `signal="trace"`, resource, scope, and span record data
- **AND** trace/span ids, timestamps, attributes, events, links, status, and dropped counts SHALL follow the documented type mapping

#### Scenario: Read log export

- **WHEN** OTLP JSON contains `resourceLogs`
- **THEN** each log record SHALL yield one row with `signal="log"`, resource, scope, severity, body, attributes, trace/span correlation, and timestamps

#### Scenario: Read metric export

- **WHEN** OTLP JSON contains `resourceMetrics`
- **THEN** each gauge, sum, histogram, exponential-histogram, or summary data point supported by the implementation SHALL yield one row
- **AND** metric name, description, unit, type, temporality/monotonicity where applicable, resource, and scope SHALL accompany the point

#### Scenario: Ordinary JSON document

- **WHEN** a JSON document lacks recognized OTLP top-level envelopes
- **THEN** content detection SHALL NOT classify it as OTLP solely because it contains similarly named nested fields

### Requirement: OTLP Protobuf Profile Reading

The system SHALL parse supported OTLP Protobuf ExportRequest messages using official message definitions and SHALL expose the same logical row envelope and values as OTLP JSON within documented mappings.

#### Scenario: Read binary export request

- **WHEN** a user explicitly opens a valid OTLP Protobuf trace, log, or metric ExportRequest
- **THEN** its individual records/data points SHALL be yielded with resource and scope context
- **AND** logical values SHALL match an equivalent OTLP JSON export

#### Scenario: Oversize binary message

- **WHEN** an OTLP Protobuf message exceeds the configured maximum size
- **THEN** parsing SHALL fail before unbounded allocation
- **AND** the error SHALL report the configured limit

#### Scenario: Dependency missing

- **WHEN** OTLP Protobuf is requested without its optional runtime/message definitions
- **THEN** an `ImportError` SHALL name the correct observability/OTLP extra

### Requirement: OTLP Type Fidelity

OTLP profiles SHALL preserve identifiers, bytes, enums, timestamps, attributes, and 64-bit integer values without lossy floating-point coercion.

#### Scenario: OTLP JSON 64-bit integer string

- **WHEN** a 64-bit integer is represented as a JSON string according to the Protobuf JSON mapping
- **THEN** reading and writing SHALL preserve its exact integer value
- **AND** SHALL NOT round it through a floating-point representation

#### Scenario: Trace and span identifiers

- **WHEN** trace/span ids move between JSON and Protobuf profiles
- **THEN** their byte values SHALL remain identical
- **AND** the row representation SHALL use the documented stable encoding

### Requirement: OTLP Profile Writing

The system SHALL write supported rows as valid OTLP JSON or Protobuf ExportRequest envelopes grouped deterministically by signal, resource, and instrumentation scope.

#### Scenario: Write and reopen mixed trace rows

- **WHEN** span rows from multiple resources/scopes are written to OTLP JSON or Protobuf
- **THEN** the writer SHALL create valid grouping envelopes
- **AND** reopening the output SHALL yield logically equivalent rows

#### Scenario: Metric type mismatch

- **WHEN** a metric point payload conflicts with its declared metric type
- **THEN** the writer SHALL raise a clear validation error
- **AND** SHALL NOT silently emit an invalid OTLP message

### Requirement: Truthful OTLP Memory Behavior

OTLP JSON SHALL parse recognized record arrays incrementally where supported. Standard single-message OTLP Protobuf inputs that require whole-message parsing SHALL declare that behavior and enforce a configured size limit.

#### Scenario: Large OTLP JSON export

- **WHEN** a large recognized OTLP JSON envelope is read
- **THEN** records SHALL be yielded without materializing all signal records as Python rows

#### Scenario: Standard Protobuf ExportRequest

- **WHEN** a single binary ExportRequest is opened
- **THEN** capability/documentation metadata SHALL identify its whole-message bound
- **AND** the maximum-message-size guard SHALL be enforced
