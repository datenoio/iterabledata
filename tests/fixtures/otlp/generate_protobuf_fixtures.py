"""Generate the committed OTLP Protobuf fixtures from the JSON fixtures.

The binary fixtures are built by parsing the conformant JSON documents with
the *official* OTLP proto message definitions (``opentelemetry-proto``) and
serializing them, so the JSON and Protobuf fixtures are logically equivalent
by construction.

Usage (repo root, with the otlp extras installed)::

    .venv/bin/python tests/fixtures/otlp/generate_protobuf_fixtures.py

Not run by pytest; regenerate intentionally when the JSON fixtures change.
"""

import json
from pathlib import Path

from google.protobuf import json_format
from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import ExportMetricsServiceRequest
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest

from iterable.datatypes.otlp import _ids_json_to_proto

HERE = Path(__file__).parent

TARGETS = {
    "traces": ExportTraceServiceRequest,
    "logs": ExportLogsServiceRequest,
    "metrics": ExportMetricsServiceRequest,
}


def main() -> None:
    for name, message_class in TARGETS.items():
        document = json.loads((HERE / f"{name}.json").read_text(encoding="utf-8"))
        message = message_class()
        json_format.ParseDict(_ids_json_to_proto(document), message)
        payload = message.SerializeToString()
        (HERE / f"{name}.pb").write_bytes(payload)
        print(f"{name}.pb: {len(payload)} bytes via {message_class.__name__}")


if __name__ == "__main__":
    main()
