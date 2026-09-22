"""OpenTelemetry Protocol (OTLP) JSON and Protobuf format profiles.

Row envelope (all profiles):

- ``signal``: ``"trace"``, ``"log"``, or ``"metric"``
- ``resource``: the OTLP Resource envelope (dict, may be empty)
- ``scope``: the instrumentation scope (dict, may be empty)
- ``record``: one span, one log record, or one metric data point

Metric rows additionally carry:

- ``metric``: ``{"name", "description", "unit"}`` context of the owning metric
- ``metric_type``: ``gauge``, ``sum``, ``histogram``, ``exponentialHistogram``,
  or ``summary``
- ``aggregation_temporality``: OTLP enum int (sum/histogram/exponentialHistogram only)
- ``is_monotonic``: bool (sum only)

Trace/span identifiers are represented as lowercase hex strings in both
profiles, following the OTLP JSON mapping (protobuf reads convert the wire
bytes to hex; protobuf writes convert hex back to bytes).
"""

from __future__ import annotations

import base64
import binascii
import json
import re
import typing
from collections import OrderedDict
from typing import Any

try:
    from google.protobuf import json_format
except ImportError:
    json_format = None

try:
    import ijson
except ImportError:
    ijson = None

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..types import Row

DEFAULT_MAX_MESSAGE_BYTES = 64 * 1024 * 1024
# Documents at or below this size are parsed eagerly (so malformed input fails
# at open/reset time). Larger documents switch to incremental parsing.
_SNIFF_CHARS = 256 * 1024

SIGNALS = ("trace", "log", "metric")
ROOT_KEYS = {"trace": "resourceSpans", "log": "resourceLogs", "metric": "resourceMetrics"}
SCOPE_KEYS = {"trace": "scopeSpans", "log": "scopeLogs", "metric": "scopeMetrics"}
RECORD_KEYS = {"trace": "spans", "log": "logRecords", "metric": "metrics"}
METRIC_POINT_KEYS = ("gauge", "sum", "histogram", "exponentialHistogram", "summary")
_TEMPORALITY_TYPES = ("sum", "histogram", "exponentialHistogram")
# Data-point keys that are only valid for a specific metric type. Used to
# reject point payloads that conflict with the declared metric type.
_POINT_SIGNATURE_KEYS = {
    "histogram": ("bucketCounts", "explicitBounds"),
    "exponentialHistogram": ("scale", "zeroCount", "positive", "negative", "zeroThreshold"),
    "summary": ("quantileValues",),
}
_ID_KEYS = ("traceId", "spanId", "parentSpanId")
_ID_HEX_LENGTHS = {"traceId": 32, "spanId": 16, "parentSpanId": 16}
_HEX_RE = re.compile(r"[0-9a-fA-F]+")
_ROOT_KEY_RE = re.compile(r'"(resourceSpans|resourceLogs|resourceMetrics)"\s*:')


# ---------------------------------------------------------------------------
# Reading helpers
# ---------------------------------------------------------------------------


def _expand_metric(metric: dict[str, Any]) -> typing.Iterator[dict[str, Any]]:
    """Yield per-data-point partial rows (without resource/scope) for a metric."""
    context = {
        "name": metric.get("name") or "",
        "description": metric.get("description") or "",
        "unit": metric.get("unit") or "",
    }
    for point_key in METRIC_POINT_KEYS:
        point = metric.get(point_key)
        if not isinstance(point, dict):
            continue
        base: dict[str, Any] = {"metric": context, "metric_type": point_key}
        if point_key in _TEMPORALITY_TYPES:
            base["aggregation_temporality"] = point.get("aggregationTemporality")
        if point_key == "sum":
            base["is_monotonic"] = point.get("isMonotonic")
        for data_point in point.get("dataPoints") or []:
            row = dict(base)
            row["metric"] = dict(context)
            row["record"] = data_point
            yield row


def _iter_signal_envelope(resource_item: dict[str, Any], signal: str) -> typing.Iterator[Row]:
    """Yield rows for a single ``resource*`` envelope of one signal."""
    resource = resource_item.get("resource") or {}
    for scope_item in resource_item.get(SCOPE_KEYS[signal]) or []:
        scope = scope_item.get("scope") or {}
        if signal == "metric":
            for metric in scope_item.get(RECORD_KEYS[signal]) or []:
                for partial in _expand_metric(metric):
                    yield {"signal": "metric", "resource": resource, "scope": scope, **partial}
        else:
            for record in scope_item.get(RECORD_KEYS[signal]) or []:
                yield {"signal": signal, "resource": resource, "scope": scope, "record": record}


def _iter_envelopes(document: dict[str, Any]) -> typing.Iterator[Row]:
    """Yield all rows of a fully parsed OTLP document."""
    for signal, root_key in ROOT_KEYS.items():
        for resource_item in document.get(root_key) or []:
            yield from _iter_signal_envelope(resource_item, signal)


class _CountingReader:
    """Bytes-returning read adapter that enforces a cumulative size limit."""

    def __init__(self, fobj: typing.IO[Any], limit: int):
        self._fobj = fobj
        self._limit = limit
        self._count = 0

    def read(self, size: int = -1) -> bytes:
        chunk = self._fobj.read(size)
        if isinstance(chunk, str):
            chunk = chunk.encode("utf-8")
        self._count += len(chunk)
        if self._count > self._limit:
            raise ValueError(
                f"OTLP JSON message exceeds max_message_bytes={self._limit}. "
                "Raise max_message_bytes or split the export into smaller documents."
            )
        return chunk


# ---------------------------------------------------------------------------
# Write helpers (shared validation and document assembly)
# ---------------------------------------------------------------------------


def _validate_hex_id(record: dict[str, Any], key: str, kind: str, required: bool) -> None:
    value = record.get(key)
    if value is None:
        if required:
            raise ValueError(
                f"OTLP {kind} is missing required identifier '{key}'. "
                f"Provide a {_ID_HEX_LENGTHS[key]}-character hex string."
            )
        return
    if not isinstance(value, str) or len(value) != _ID_HEX_LENGTHS[key] or not _HEX_RE.fullmatch(value):
        raise ValueError(f"OTLP {kind} '{key}' must be a {_ID_HEX_LENGTHS[key]}-character hex string; got {value!r}.")


def _validate_trace_record(record: Any) -> None:
    if not isinstance(record, dict):
        raise TypeError(f"OTLP span record must be a dict; got {type(record).__name__}.")
    _validate_hex_id(record, "traceId", "span", required=True)
    _validate_hex_id(record, "spanId", "span", required=True)
    _validate_hex_id(record, "parentSpanId", "span", required=False)


def _validate_log_record(record: Any) -> None:
    if not isinstance(record, dict):
        raise TypeError(f"OTLP log record must be a dict; got {type(record).__name__}.")
    _validate_hex_id(record, "traceId", "log record", required=False)
    _validate_hex_id(record, "spanId", "log record", required=False)


def _validate_metric_row(row: Row) -> dict[str, Any]:
    """Validate a metric row and return its normalized identity parts."""
    metric = row.get("metric")
    if not isinstance(metric, dict):
        raise TypeError(
            "OTLP metric row must carry a 'metric' context dict with 'name', "
            f"'description', and 'unit'; got {type(metric).__name__}."
        )
    name = metric.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError(f"OTLP metric requires a non-empty string 'name'; got {name!r}.")
    metric_type = row.get("metric_type")
    if metric_type not in METRIC_POINT_KEYS:
        raise ValueError(f"OTLP metric 'metric_type' must be one of {METRIC_POINT_KEYS}; got {metric_type!r}.")
    data_point = row.get("record")
    if not isinstance(data_point, dict):
        raise TypeError(f"OTLP metric 'record' (data point) must be a dict; got {type(data_point).__name__}.")

    temporality = row.get("aggregation_temporality")
    monotonic = row.get("is_monotonic")
    if metric_type in _TEMPORALITY_TYPES:
        if not isinstance(temporality, int) or isinstance(temporality, bool):
            raise ValueError(
                f"OTLP {metric_type} metric '{name}' requires integer 'aggregation_temporality' "
                f"(1=DELTA, 2=CUMULATIVE); got {temporality!r}."
            )
    elif temporality is not None:
        raise ValueError(
            f"OTLP {metric_type} metric '{name}' must not set 'aggregation_temporality'; "
            "it is only valid for sum/histogram/exponentialHistogram."
        )
    if metric_type == "sum":
        if not isinstance(monotonic, bool):
            raise ValueError(f"OTLP sum metric '{name}' requires boolean 'is_monotonic'; got {monotonic!r}.")
    elif monotonic is not None:
        raise ValueError(f"OTLP {metric_type} metric '{name}' must not set 'is_monotonic'; it is only valid for sum.")

    # Point/type compatibility: reject keys that belong to another metric type.
    for other_type, keys in _POINT_SIGNATURE_KEYS.items():
        if other_type == metric_type:
            continue
        for key in keys:
            if key in data_point:
                raise ValueError(
                    f"OTLP metric '{name}': data point key '{key}' belongs to "
                    f"'{other_type}' points but the row declares metric_type='{metric_type}'. "
                    "Fix the metric_type or the data point payload."
                )
    return {
        "name": name,
        "description": metric.get("description") or "",
        "unit": metric.get("unit") or "",
        "metric_type": metric_type,
        "aggregation_temporality": temporality,
        "is_monotonic": monotonic,
    }


def _build_metric_object(identity: dict[str, Any]) -> dict[str, Any]:
    metric_type = identity["metric_type"]
    obj: dict[str, Any] = {"name": identity["name"]}
    if identity["description"]:
        obj["description"] = identity["description"]
    if identity["unit"]:
        obj["unit"] = identity["unit"]
    point: dict[str, Any] = {"dataPoints": []}
    if metric_type in _TEMPORALITY_TYPES:
        point["aggregationTemporality"] = identity["aggregation_temporality"]
    if metric_type == "sum":
        point["isMonotonic"] = identity["is_monotonic"]
    obj[metric_type] = point
    return obj


def _group_rows(records: list[Row]) -> OrderedDict[str, OrderedDict[tuple[str, str], Any]]:
    """Group rows deterministically by signal, resource, and scope.

    Trace/log groups collect raw records; metric groups collect per-metric
    objects keyed by metric identity so data points merge correctly.
    """
    grouped: OrderedDict[str, OrderedDict[tuple[str, str], Any]] = OrderedDict(
        (signal, OrderedDict()) for signal in SIGNALS
    )
    metric_identity_keys = ("name", "description", "unit", "metric_type", "aggregation_temporality", "is_monotonic")
    for row in records:
        signal = row.get("signal")
        if signal not in SIGNALS:
            raise ValueError(f"OTLP row 'signal' must be one of {SIGNALS}; got {signal!r}.")
        resource = row.get("resource") or {}
        scope = row.get("scope") or {}
        if not isinstance(resource, dict):
            raise TypeError(f"OTLP row 'resource' must be a dict; got {type(resource).__name__}.")
        if not isinstance(scope, dict):
            raise TypeError(f"OTLP row 'scope' must be a dict; got {type(scope).__name__}.")
        group_key = (
            json.dumps(resource, sort_keys=True, ensure_ascii=False),
            json.dumps(scope, sort_keys=True, ensure_ascii=False),
        )
        if signal == "metric":
            identity = _validate_metric_row(row)
            metrics = grouped["metric"].setdefault(group_key, OrderedDict())
            metric_key = json.dumps({k: identity[k] for k in metric_identity_keys}, sort_keys=True)
            metric_obj = metrics.get(metric_key)
            if metric_obj is None:
                metric_obj = _build_metric_object(identity)
                metrics[metric_key] = metric_obj
            metric_obj[identity["metric_type"]]["dataPoints"].append(row["record"])
        else:
            if signal == "trace":
                _validate_trace_record(row.get("record"))
            else:
                _validate_log_record(row.get("record"))
            grouped[signal].setdefault(group_key, []).append(row["record"])
    return grouped


def _build_document(records: list[Row]) -> dict[str, Any]:
    """Assemble a validated OTLP document from rows."""
    grouped = _group_rows(records)
    document: dict[str, Any] = OrderedDict()
    for signal in SIGNALS:
        items = []
        for (resource_json, scope_json), payload in grouped[signal].items():
            record_payload = list(payload.values()) if signal == "metric" else payload
            items.append(
                {
                    "resource": json.loads(resource_json),
                    SCOPE_KEYS[signal]: [{"scope": json.loads(scope_json), RECORD_KEYS[signal]: record_payload}],
                }
            )
        document[ROOT_KEYS[signal]] = items
    return document


# ---------------------------------------------------------------------------
# Protobuf id conversion (OTLP JSON uses hex ids; protobuf JSON uses base64)
# ---------------------------------------------------------------------------


def _convert_ids(obj: Any, func: Any) -> Any:
    if isinstance(obj, dict):
        converted = {}
        for key, value in obj.items():
            if key in _ID_KEYS and isinstance(value, str) and value:
                converted[key] = func(value)
            else:
                converted[key] = _convert_ids(value, func)
        return converted
    if isinstance(obj, list):
        return [_convert_ids(item, func) for item in obj]
    return obj


def _b64_to_hex(value: str) -> str:
    try:
        return base64.b64decode(value).hex()
    except (binascii.Error, ValueError):
        return value


def _hex_to_b64(value: str) -> str:
    try:
        return base64.b64encode(bytes.fromhex(value)).decode("ascii")
    except ValueError:
        return value


def _ids_proto_to_json(document: dict[str, Any]) -> dict[str, Any]:
    return typing.cast(dict[str, Any], _convert_ids(document, _b64_to_hex))


def _ids_json_to_proto(document: dict[str, Any]) -> dict[str, Any]:
    return typing.cast(dict[str, Any], _convert_ids(document, _hex_to_b64))


# ---------------------------------------------------------------------------
# Iterables
# ---------------------------------------------------------------------------


class OTLPJSONIterable(BaseFileIterable):
    """OTLP JSON reader/writer for traces, logs, and metrics export envelopes.

    Reading is incremental for recognized envelopes on seekable sources when
    the optional ``ijson`` dependency is installed: one resource envelope is
    materialized at a time and individual records are yielded as rows. Small
    documents (and non-seekable streams) are parsed eagerly so malformed input
    fails at open time. Both paths are bounded by ``max_message_bytes``.
    """

    datamode = "text"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        max_message_bytes: int = DEFAULT_MAX_MESSAGE_BYTES,
        options: dict[str, Any] | None = None,
    ):
        self.max_message_bytes = max_message_bytes
        self.item_key = (options or {}).get("item_key")
        self._rows: list[Row] | None = None
        self._row_iter: typing.Iterator[Row] = iter(())
        self._streaming = False
        self._stream_roots: tuple[str, ...] = ()
        self._pending: list[Row] = []
        self._flushed = False
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

    def _size_check(self, size: int) -> None:
        if size > self.max_message_bytes:
            raise ValueError(
                f"OTLP JSON message exceeds max_message_bytes={self.max_message_bytes}. "
                "Raise max_message_bytes or split the export into smaller documents."
            )

    def _parse_document(self, payload: str) -> dict[str, Any]:
        try:
            document = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid OTLP JSON: {exc}") from exc
        if not isinstance(document, dict):
            raise ValueError(f"OTLP JSON root must be an object; got {type(document).__name__}.")
        if self.item_key:
            nested = document.get(self.item_key)
            if not isinstance(nested, dict):
                raise ValueError(
                    f"OTLP JSON item_key '{self.item_key}' must select a nested object containing the OTLP envelope."
                )
            document = nested
        return document

    def _init_rows(self) -> None:
        fobj = self.fobj
        seekable = False
        try:
            seekable = bool(fobj.seekable())
        except Exception:
            seekable = False

        peek = fobj.read(_SNIFF_CHARS + 1) if seekable else None
        if peek is not None:
            fobj.seek(0)
            if isinstance(peek, bytes):
                peek = peek.decode("utf-8", errors="replace")

        if peek is not None and len(peek) <= _SNIFF_CHARS:
            # Small document: parse eagerly so malformed input fails at reset.
            payload = peek
            if not payload.strip():
                self._rows = []
            else:
                self._size_check(len(payload.encode("utf-8")))
                self._rows = list(_iter_envelopes(self._parse_document(payload)))
            self._row_iter = iter(self._rows)
            return

        if seekable and ijson is not None:
            # Large document: stream recognized envelopes incrementally.
            self._streaming = True
            self._stream_roots = tuple(OrderedDict.fromkeys(_ROOT_KEY_RE.findall(peek)))
            self._rows = None
            self._row_iter = self._stream_rows()
            return

        # Non-seekable stream or no ijson: bounded whole-document fallback.
        rest = fobj.read(self.max_message_bytes + 1)
        payload = ((peek or "") + rest) if peek is not None else rest
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8", errors="replace")
        self._size_check(len(payload.encode("utf-8")))
        if not payload.strip():
            self._rows = []
        else:
            self._rows = list(_iter_envelopes(self._parse_document(payload)))
        self._row_iter = iter(self._rows)

    def _stream_rows(self) -> typing.Iterator[Row]:
        signal_by_root = {v: k for k, v in ROOT_KEYS.items()}
        for root_key in self._stream_roots:
            prefix = f"{self.item_key}.{root_key}.item" if self.item_key else f"{root_key}.item"
            self.fobj.seek(0)
            reader = _CountingReader(self.fobj, self.max_message_bytes)
            try:
                for resource_item in ijson.items(reader, prefix):
                    yield from _iter_signal_envelope(resource_item, signal_by_root[root_key])
            except ValueError:
                raise
            except Exception as exc:
                raise ValueError(f"Invalid OTLP JSON: {exc}") from exc

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        self._streaming = False
        self._stream_roots = ()
        self._rows = None
        self._row_iter = iter(())
        if self.mode == "r":
            self._init_rows()
        else:
            self._pending = []
            self._flushed = False

    @staticmethod
    def has_totals() -> bool:
        return True

    def totals(self) -> int:
        if self.mode != "r":
            return 0
        if not self._streaming:
            return len(self._rows or [])
        # Streaming sources have no cheap total; count with fresh passes and
        # restore a clean iterator afterwards.
        count = 0
        for _ in self._stream_rows():
            count += 1
        self.pos = 0
        self._row_iter = self._stream_rows()
        return count

    def read(self, skip_empty: bool = True) -> Row:
        row = next(self._row_iter)
        self.pos += 1
        return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[Row]:
        rows: list[Row] = []
        for _ in range(num):
            try:
                rows.append(self.read())
            except StopIteration:
                break
        return rows

    def write(self, record: Row) -> None:
        self.write_bulk([record])

    def write_bulk(self, records: list[Row]) -> None:
        if self._flushed:
            raise ValueError(
                "OTLP JSON document was already finalized on close/flush; write all rows before closing the iterable."
            )
        self._pending.extend(records)

    def _flush_document(self) -> None:
        if self.mode != "r" and not self._flushed:
            self._flushed = True
            document = _build_document(self._pending)
            self._write_document(document)

    def _write_document(self, document: dict[str, Any]) -> None:
        encoded = json.dumps(document, ensure_ascii=False, separators=(",", ":"))
        self._size_check(len(encoded.encode("utf-8")))
        self.fobj.write(encoded)

    def flush(self) -> None:
        """Finalize the output document without closing the underlying stream."""
        self._flush_document()
        if hasattr(self.fobj, "flush"):
            self.fobj.flush()

    def close(self) -> None:
        self._flush_document()
        super().close()


class OTLPProtobufIterable(OTLPJSONIterable):
    """OTLP Protobuf profile for a single binary ExportRequest message.

    Requires an explicit generated ``message_class`` (for example
    ``ExportTraceServiceRequest`` from the ``opentelemetry-proto`` package).
    A standard ExportRequest is one protobuf message, so reading and writing
    are whole-message operations bounded by ``max_message_bytes``.
    """

    datamode = "binary"

    def __init__(self, *args: Any, message_class: Any = None, **kwargs: Any):
        if json_format is None:
            raise ImportError(
                "OTLP Protobuf support requires the 'protobuf' package. "
                "Install it with: pip install 'iterabledata[otlp]'"
            )
        options = kwargs.get("options") or {}
        self.message_class = message_class or options.get("message_class")
        if self.message_class is None:
            raise ValueError(
                "OTLP Protobuf requires message_class, e.g. "
                "opentelemetry.proto.collector.trace.v1.trace_service_pb2.ExportTraceServiceRequest. "
                "Binary OTLP has no reliable magic signature, so the message type cannot be guessed."
            )
        # ``_construct`` forwards superset kwargs (binary/encoding/noopen) that
        # the JSON parent's signature does not accept; drop them here.
        for extra_key in ("binary", "encoding", "noopen"):
            kwargs.pop(extra_key, None)
        super().__init__(*args, **kwargs)

    @staticmethod
    def id() -> str:
        return "otlp-protobuf"

    def _init_rows(self) -> None:
        payload = self.fobj.read(self.max_message_bytes + 1)
        if len(payload) > self.max_message_bytes:
            raise ValueError(
                f"OTLP Protobuf message exceeds max_message_bytes={self.max_message_bytes}. "
                "Raise max_message_bytes or split the export into smaller messages."
            )
        if not payload:
            self._rows = []
        else:
            message = self.message_class()
            try:
                message.ParseFromString(payload)
            except Exception as exc:
                raise ValueError(f"Invalid OTLP Protobuf message for {self.message_class.__name__}: {exc}") from exc
            document = json_format.MessageToDict(message, use_integers_for_enums=True)
            self._rows = list(_iter_envelopes(_ids_proto_to_json(document)))
        self._row_iter = iter(self._rows)

    def _write_document(self, document: dict[str, Any]) -> None:
        message = self.message_class()
        # Signal-specific ExportRequest messages only declare their own root
        # field (e.g. ExportTraceServiceRequest has only resourceSpans), so
        # drop keys the message type does not know.
        known_fields = {field.json_name for field in message.DESCRIPTOR.fields}
        known_fields.update(field.name for field in message.DESCRIPTOR.fields)
        filtered = {key: value for key, value in document.items() if key in known_fields}
        # Empty resource/scope dicts would set proto presence bits that a
        # minimal export never had; drop them for faithful serialization.
        scope_key_by_root = {ROOT_KEYS[signal]: SCOPE_KEYS[signal] for signal in SIGNALS}
        for root_key, items in filtered.items():
            scope_key = scope_key_by_root.get(root_key)
            for item in items:
                if item.get("resource") == {}:
                    item.pop("resource", None)
                if scope_key:
                    for scope_item in item.get(scope_key) or []:
                        if scope_item.get("scope") == {}:
                            scope_item.pop("scope", None)
        try:
            json_format.ParseDict(_ids_json_to_proto(filtered), message)
        except Exception as exc:
            raise ValueError(f"Rows cannot be encoded as {self.message_class.__name__}: {exc}") from exc
        payload = message.SerializeToString()
        if len(payload) > self.max_message_bytes:
            raise ValueError(
                f"OTLP Protobuf message exceeds max_message_bytes={self.max_message_bytes}. "
                "Raise max_message_bytes or split the export into smaller messages."
            )
        self.fobj.write(payload)
