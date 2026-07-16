"""OpenTelemetry Protocol JSON and Protobuf profiles."""

from __future__ import annotations

import io
import json
import typing
from collections import OrderedDict, defaultdict
from typing import Any

try:
    from google.protobuf import json_format
except ImportError:
    json_format = None

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..types import Row

SIGNALS = ("traces", "logs", "metrics")
ROOT_KEYS = {"traces": "resourceSpans", "logs": "resourceLogs", "metrics": "resourceMetrics"}


def _iter_envelopes(document: dict[str, Any]):
    for signal, root_key in ROOT_KEYS.items():
        for resource_item in document.get(root_key, []):
            resource = resource_item.get("resource", {})
            scope_key = {"traces": "scopeSpans", "logs": "scopeLogs", "metrics": "scopeMetrics"}[signal]
            record_key = {"traces": "spans", "logs": "logRecords", "metrics": "metric"}[signal]
            for scope_item in resource_item.get(scope_key, []):
                scope = scope_item.get("scope", {})
                records = scope_item.get(record_key, [])
                if signal == "metrics":
                    records = _metric_records(records)
                for record in records:
                    yield {
                        "signal": signal,
                        "resource": resource,
                        "scope": scope,
                        "record": record,
                    }


def _metric_records(metrics: list[dict[str, Any]]):
    for metric in metrics:
        for point_key in ("gauge", "sum", "histogram", "exponentialHistogram", "summary"):
            point = metric.get(point_key)
            if point is None:
                continue
            data_points = point.get("dataPoints", point.get("data_points", []))
            for data_point in data_points:
                yield {"metric": metric, "metric_type": point_key, "data_point": data_point}


class OTLPJSONIterable(BaseFileIterable):
    """OTLP JSON document or one-document-per-line reader/writer."""

    datamode = "text"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        max_message_bytes: int = 64 * 1024 * 1024,
        options: dict[str, Any] | None = None,
    ):
        self.max_message_bytes = max_message_bytes
        self.item_key = (options or {}).get("item_key")
        self._rows: list[Row] = []
        super().__init__(
            filename,
            stream,
            codec=codec,
            mode=mode,
            binary=self.datamode == "binary",
            encoding="utf8",
            options=options or {},
        )
        self.reset()

    @staticmethod
    def id() -> str:
        return "otlp-json"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def is_streaming(self) -> bool:
        return True

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        self._rows = []
        if self.mode == "r":
            payload = self.fobj.read(self.max_message_bytes + 1)
            if len(payload.encode("utf-8") if isinstance(payload, str) else payload) > self.max_message_bytes:
                raise ValueError(f"OTLP JSON message exceeds max_message_bytes={self.max_message_bytes}")
            if not payload:
                return
            try:
                if self.item_key:
                    document = json.loads(payload)
                    document = {self.item_key: document[self.item_key]}
                else:
                    document = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid OTLP JSON: {exc}") from exc
            if not isinstance(document, dict):
                raise ValueError("OTLP JSON root must be an object")
            self._rows = list(_iter_envelopes(document))

    @staticmethod
    def has_totals() -> bool:
        return True

    def totals(self) -> int:
        return len(self._rows) if self.mode == "r" else 0

    def read(self, skip_empty: bool = True) -> Row:
        if self.pos >= len(self._rows):
            raise StopIteration
        row = self._rows[self.pos]
        self.pos += 1
        return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[Row]:
        end = min(self.pos + num, len(self._rows))
        rows = self._rows[self.pos : end]
        self.pos = end
        return rows

    def write(self, record: Row) -> None:
        self.write_bulk([record])

    def write_bulk(self, records: list[Row]) -> None:
        grouped: dict[str, dict[tuple[str, str], list[Row]]] = defaultdict(lambda: defaultdict(list))
        for record in records:
            signal = record.get("signal")
            if signal not in SIGNALS:
                raise ValueError(f"OTLP row signal must be one of {SIGNALS}")
            resource_key = json.dumps(record.get("resource", {}), sort_keys=True)
            scope_key = json.dumps(record.get("scope", {}), sort_keys=True)
            grouped[signal][(resource_key, scope_key)].append(record["record"])
        document: dict[str, Any] = OrderedDict()
        for signal in SIGNALS:
            root_key = ROOT_KEYS[signal]
            scope_key = {"traces": "scopeSpans", "logs": "scopeLogs", "metrics": "scopeMetrics"}[signal]
            record_key = {"traces": "spans", "logs": "logRecords", "metrics": "metric"}[signal]
            items = []
            for (resource_key, scope_key_json), records_for_scope in grouped[signal].items():
                items.append(
                    {
                        "resource": json.loads(resource_key),
                        scope_key: [{"scope": json.loads(scope_key_json), record_key: records_for_scope}],
                    }
                )
            document[root_key] = items
        encoded = json.dumps(document, ensure_ascii=False, separators=(",", ":"))
        if len(encoded.encode("utf-8")) > self.max_message_bytes:
            raise ValueError(f"OTLP JSON message exceeds max_message_bytes={self.max_message_bytes}")
        self.fobj.write(encoded)


class OTLPProtobufIterable(OTLPJSONIterable):
    """OTLP ExportRequest profile using an explicitly supplied protobuf class."""

    datamode = "binary"

    def __init__(self, *args: Any, message_class: Any = None, **kwargs: Any):
        if json_format is None:
            raise ImportError("OTLP Protobuf support requires protobuf")
        self.message_class = message_class or kwargs.pop("options", {}).get("message_class")
        if self.message_class is None:
            raise ValueError(
                "OTLP Protobuf requires message_class=ExportTraceServiceRequest/ExportLogsServiceRequest/etc."
            )
        super().__init__(*args, **kwargs)

    @staticmethod
    def id() -> str:
        return "otlp-protobuf"

    def reset(self) -> None:
        BaseFileIterable.reset(self)
        self.pos = 0
        self._rows = []
        if self.mode == "r":
            payload = self.fobj.read(self.max_message_bytes + 1)
            if len(payload) > self.max_message_bytes:
                raise ValueError(f"OTLP Protobuf message exceeds max_message_bytes={self.max_message_bytes}")
            if payload:
                message = self.message_class()
                message.ParseFromString(payload)
                self._rows = list(_iter_envelopes(json_format.MessageToDict(message, preserving_proto_field_name=True)))

    def write_bulk(self, records: list[Row]) -> None:
        # Reuse the canonical JSON grouping, then let protobuf's official
        # descriptor perform type/enum/bytes validation.
        temp_stream = io.StringIO()
        temp = OTLPJSONIterable.from_stream(temp_stream, mode="w")
        temp.write_bulk(records)
        message = self.message_class()
        json_format.ParseDict(json.loads(temp_stream.getvalue()), message)
        payload = message.SerializeToString()
        if len(payload) > self.max_message_bytes:
            raise ValueError(f"OTLP Protobuf message exceeds max_message_bytes={self.max_message_bytes}")
        self.fobj.write(payload)
