"""Tests for the OTLP JSON and Protobuf format profiles."""

import io
import json
import tracemalloc
from pathlib import Path

import pytest

import iterable.datatypes.otlp as otlp_module
from iterable.datatypes.otlp import OTLPJSONIterable, OTLPProtobufIterable

FIXTURES = Path("fixtures/otlp")

TRACE_ID = "5b8aa5a2d2c872e8321cf37308d69df2"
SPAN_ID = "051581bf3cb55c13"

protobuf = pytest.importorskip("google.protobuf", reason="protobuf extra not installed")
otel_proto = pytest.importorskip("opentelemetry.proto", reason="opentelemetry-proto not installed")

from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest  # noqa: E402
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import (  # noqa: E402
    ExportMetricsServiceRequest,
)
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (  # noqa: E402
    ExportTraceServiceRequest,
)

SIGNAL_MESSAGE_CLASS = {
    "traces": ExportTraceServiceRequest,
    "logs": ExportLogsServiceRequest,
    "metrics": ExportMetricsServiceRequest,
}


def _read_json(path):
    return list(OTLPJSONIterable.from_file(str(path)))


def _read_pb(source, message_class):
    if hasattr(source, "read"):
        return list(OTLPProtobufIterable.from_stream(source, message_class=message_class))
    return list(OTLPProtobufIterable.from_file(str(source), message_class=message_class))


def _write_json(rows):
    stream = io.StringIO()
    writer = OTLPJSONIterable.from_stream(stream, mode="w")
    writer.write_bulk(rows)
    writer.flush()
    return stream.getvalue()


def _write_pb(rows, message_class):
    stream = io.BytesIO()
    writer = OTLPProtobufIterable.from_stream(stream, mode="w", message_class=message_class)
    writer.write_bulk(rows)
    writer.flush()
    return stream.getvalue()


def _span_row(**overrides):
    row = {
        "signal": "trace",
        "resource": {},
        "scope": {},
        "record": {"traceId": TRACE_ID, "spanId": SPAN_ID, "name": "op"},
    }
    row.update(overrides)
    return row


def _metric_row(metric_type="gauge", point=None, **overrides):
    row = {
        "signal": "metric",
        "resource": {},
        "scope": {},
        "metric": {"name": "m", "description": "", "unit": "1"},
        "metric_type": metric_type,
        "record": point if point is not None else {"asInt": "1"},
    }
    row.update(overrides)
    return row


def _large_trace_document(envelopes=200, spans_per_envelope=10):
    """Document above the eager-parse threshold with many small envelopes."""
    return {
        "resourceSpans": [
            {
                "resource": {"attributes": [{"key": "idx", "value": {"intValue": str(i)}}]},
                "scopeSpans": [
                    {
                        "scope": {"name": "gen"},
                        "spans": [
                            {
                                "traceId": f"{i:016x}{j:016x}",
                                "spanId": f"{j:016x}",
                                "name": f"span-{i}-{j}",
                                "startTimeUnixNano": "1544712660000000000",
                            }
                            for j in range(spans_per_envelope)
                        ],
                    }
                ],
            }
            for i in range(envelopes)
        ]
    }


class TestOTLPJSONFixtures:
    def test_traces_fixture_rows(self):
        rows = _read_json(FIXTURES / "traces.json")
        assert len(rows) == 3
        first = rows[0]
        assert first["signal"] == "trace"
        assert first["resource"]["attributes"][0]["value"]["stringValue"] == "checkout"
        assert first["scope"]["name"] == "shopping.cart"
        record = first["record"]
        assert record["traceId"] == TRACE_ID
        assert record["spanId"] == SPAN_ID
        assert record["kind"] == 2
        # 64-bit timestamps stay exact strings (no float coercion)
        assert record["startTimeUnixNano"] == "1544712660000000000"
        assert record["events"][0]["name"] == "queue.dequeued"
        assert record["links"][0]["traceId"] == "7c8b16219a73ccaea8bc75ca1f849a3e"
        assert record["droppedLinksCount"] == 2
        # second resource/scope grouping preserved
        assert rows[2]["resource"]["attributes"][0]["value"]["stringValue"] == "billing"
        assert rows[2]["record"]["kind"] == 3

    def test_logs_fixture_rows(self):
        rows = _read_json(FIXTURES / "logs.json")
        assert len(rows) == 2
        first, second = rows
        assert first["signal"] == "log"
        assert first["record"]["severityNumber"] == 9
        assert first["record"]["body"] == {"stringValue": "checkout started"}
        assert first["record"]["traceId"] == TRACE_ID
        assert first["record"]["attributes"][1]["value"] == {"bytesValue": "AAEC"}
        assert second["record"]["severityText"] == "ERROR"
        assert "traceId" not in second["record"]

    def test_metrics_fixture_all_variants(self):
        rows = _read_json(FIXTURES / "metrics.json")
        by_type = {}
        for row in rows:
            assert row["signal"] == "metric"
            by_type.setdefault(row["metric_type"], []).append(row)
        assert set(by_type) == {"gauge", "sum", "histogram", "exponentialHistogram", "summary"}

        gauge = by_type["gauge"][0]
        assert gauge["metric"]["name"] == "system.cpu.utilization"
        assert gauge["metric"]["unit"] == "1"
        assert gauge["record"]["exemplars"][0]["traceId"] == TRACE_ID

        total = by_type["sum"][0]
        assert total["aggregation_temporality"] == 2
        assert total["is_monotonic"] is True
        # 2**53 + 1: must survive exactly, never rounded through float
        assert total["record"]["asInt"] == "9007199254740993"

        histogram = by_type["histogram"][0]
        assert histogram["aggregation_temporality"] == 1
        assert histogram["record"]["bucketCounts"] == ["2", "1"]
        assert histogram["record"]["count"] == "3"

        exp_histogram = by_type["exponentialHistogram"][0]
        assert exp_histogram["aggregation_temporality"] == 2
        assert exp_histogram["record"]["positive"]["bucketCounts"] == ["2", "1"]

        summary = by_type["summary"][0]
        assert summary["record"]["quantileValues"][1] == {"quantile": 0.99, "value": 42.0}

    def test_protobuf_fixtures_rows(self):
        assert len(_read_pb(FIXTURES / "traces.pb", ExportTraceServiceRequest)) == 3
        assert len(_read_pb(FIXTURES / "logs.pb", ExportLogsServiceRequest)) == 2
        assert len(_read_pb(FIXTURES / "metrics.pb", ExportMetricsServiceRequest)) == 6


class TestJSONProtobufEquivalence:
    @pytest.mark.parametrize("signal", ["traces", "logs", "metrics"])
    def test_fixture_logical_equivalence(self, signal):
        json_rows = _read_json(FIXTURES / f"{signal}.json")
        pb_rows = _read_pb(FIXTURES / f"{signal}.pb", SIGNAL_MESSAGE_CLASS[signal])
        assert json_rows == pb_rows

    @pytest.mark.parametrize("signal", ["traces", "logs", "metrics"])
    def test_json_round_trip(self, signal):
        rows = _read_json(FIXTURES / f"{signal}.json")
        reread = list(OTLPJSONIterable.from_stream(io.StringIO(_write_json(rows))))
        assert reread == rows

    @pytest.mark.parametrize("signal", ["traces", "logs", "metrics"])
    def test_protobuf_strict_round_trip(self, signal):
        message_class = SIGNAL_MESSAGE_CLASS[signal]
        original_payload = (FIXTURES / f"{signal}.pb").read_bytes()
        rows = _read_pb(FIXTURES / f"{signal}.pb", message_class)
        rewritten = _write_pb(rows, message_class)
        original, copy = message_class(), message_class()
        original.ParseFromString(original_payload)
        copy.ParseFromString(rewritten)
        assert copy == original

    @pytest.mark.parametrize("signal", ["traces", "logs", "metrics"])
    def test_json_rows_via_protobuf_round_trip(self, signal):
        rows = _read_json(FIXTURES / f"{signal}.json")
        payload = _write_pb(rows, SIGNAL_MESSAGE_CLASS[signal])
        reread = _read_pb(io.BytesIO(payload), SIGNAL_MESSAGE_CLASS[signal])
        assert reread == rows


class TestWriteValidation:
    def test_unknown_signal_rejected(self):
        with pytest.raises(ValueError, match="signal"):
            _write_json([{"signal": "events", "resource": {}, "scope": {}, "record": {}}])

    def test_span_requires_trace_and_span_ids(self):
        row = _span_row()
        del row["record"]["traceId"]
        with pytest.raises(ValueError, match="traceId"):
            _write_json([row])
        row = _span_row()
        del row["record"]["spanId"]
        with pytest.raises(ValueError, match="spanId"):
            _write_json([row])

    def test_span_id_must_be_hex_of_correct_length(self):
        row = _span_row()
        row["record"]["traceId"] = "zz" * 16
        with pytest.raises(ValueError, match="32-character hex"):
            _write_json([row])
        row = _span_row()
        row["record"]["spanId"] = "abc"
        with pytest.raises(ValueError, match="16-character hex"):
            _write_json([row])

    def test_log_correlation_ids_validated_when_present(self):
        row = {"signal": "log", "resource": {}, "scope": {}, "record": {"body": {"stringValue": "x"}}}
        _write_json([row])  # ids optional for logs
        row["record"]["traceId"] = "not-hex"
        with pytest.raises(ValueError, match="traceId"):
            _write_json([row])

    def test_record_type_errors(self):
        with pytest.raises(TypeError, match="dict"):
            _write_json([{"signal": "trace", "resource": {}, "scope": {}, "record": "nope"}])

    def test_metric_requires_name(self):
        row = _metric_row()
        row["metric"]["name"] = ""
        with pytest.raises(ValueError, match="name"):
            _write_json([row])

    def test_metric_unknown_type_rejected(self):
        with pytest.raises(ValueError, match="metric_type"):
            _write_json([_metric_row(metric_type="counter")])

    def test_sum_requires_temporality_and_monotonicity(self):
        with pytest.raises(ValueError, match="aggregation_temporality"):
            _write_json([_metric_row(metric_type="sum", is_monotonic=True)])
        with pytest.raises(ValueError, match="is_monotonic"):
            _write_json([_metric_row(metric_type="sum", aggregation_temporality=2)])
        rows = _write_json([_metric_row(metric_type="sum", aggregation_temporality=2, is_monotonic=False)])
        assert '"sum"' in rows

    def test_gauge_rejects_temporality(self):
        with pytest.raises(ValueError, match="must not set 'aggregation_temporality'"):
            _write_json([_metric_row(metric_type="gauge", aggregation_temporality=2)])

    def test_metric_point_type_conflict_rejected(self):
        # quantileValues belongs to summary points only
        with pytest.raises(ValueError, match="summary"):
            _write_json([_metric_row(metric_type="gauge", point={"quantileValues": []})])
        # bucketCounts belongs to histogram points only
        with pytest.raises(ValueError, match="histogram"):
            _write_json(
                [
                    _metric_row(
                        metric_type="sum", aggregation_temporality=1, is_monotonic=True, point={"bucketCounts": ["1"]}
                    )
                ]
            )

    def test_write_after_close_rejected(self):
        stream = io.StringIO()
        writer = OTLPJSONIterable.from_stream(stream, mode="w")
        writer.write(_span_row())
        writer.flush()
        with pytest.raises(ValueError, match="finalized"):
            writer.write(_span_row())

    def test_metric_points_merge_per_metric(self):
        rows = [
            _metric_row(metric_type="sum", aggregation_temporality=2, is_monotonic=True, point={"asInt": "1"}),
            _metric_row(metric_type="sum", aggregation_temporality=2, is_monotonic=True, point={"asInt": "2"}),
        ]
        document = json.loads(_write_json(rows))
        metrics = document["resourceMetrics"][0]["scopeMetrics"][0]["metrics"]
        assert len(metrics) == 1
        assert [p["asInt"] for p in metrics[0]["sum"]["dataPoints"]] == ["1", "2"]

    def test_grouping_by_resource_and_scope(self):
        rows = [
            _span_row(resource={"attributes": [{"key": "svc", "value": {"stringValue": "a"}}]}),
            _span_row(resource={"attributes": [{"key": "svc", "value": {"stringValue": "b"}}]}),
        ]
        document = json.loads(_write_json(rows))
        assert len(document["resourceSpans"]) == 2


class TestMalformedAndLimits:
    def test_invalid_json_rejected_at_open(self):
        with pytest.raises(ValueError, match="Invalid OTLP JSON"):
            OTLPJSONIterable.from_stream(io.StringIO("{not json"))

    def test_non_object_root_rejected(self):
        with pytest.raises(ValueError, match="root must be an object"):
            OTLPJSONIterable.from_stream(io.StringIO("[1, 2]"))

    def test_empty_input_yields_no_rows(self):
        source = OTLPJSONIterable.from_stream(io.StringIO(""))
        assert source.totals() == 0
        with pytest.raises(StopIteration):
            source.read()
        empty_pb = OTLPProtobufIterable.from_stream(io.BytesIO(b""), message_class=ExportTraceServiceRequest)
        assert list(empty_pb) == []

    def test_json_size_limit_enforced(self):
        payload = json.dumps({"resourceSpans": []})
        with pytest.raises(ValueError, match="max_message_bytes=4"):
            OTLPJSONIterable.from_stream(io.StringIO(payload), max_message_bytes=4)

    def test_protobuf_size_limit_enforced(self):
        payload = (FIXTURES / "traces.pb").read_bytes()
        with pytest.raises(ValueError, match="max_message_bytes=16"):
            OTLPProtobufIterable.from_stream(
                io.BytesIO(payload), message_class=ExportTraceServiceRequest, max_message_bytes=16
            )

    def test_protobuf_garbage_rejected(self):
        with pytest.raises(ValueError, match="Invalid OTLP Protobuf"):
            OTLPProtobufIterable.from_stream(
                io.BytesIO(b"\xff\xff\xff\xff\xff"), message_class=ExportTraceServiceRequest
            )

    def test_missing_message_class_rejected(self):
        with pytest.raises(ValueError, match="message_class"):
            OTLPProtobufIterable.from_stream(io.BytesIO(b""))

    def test_missing_protobuf_dependency_raises_import_error(self, monkeypatch):
        monkeypatch.setattr(otlp_module, "json_format", None)
        with pytest.raises(ImportError, match=r"iterabledata\[otlp\]"):
            OTLPProtobufIterable.from_stream(io.BytesIO(b""), message_class=ExportTraceServiceRequest)

    def test_unknown_json_fields_preserved(self):
        row = _span_row()
        row["record"]["vendorExtension"] = {"anything": [1, 2]}
        document = json.loads(_write_json([row]))
        span = document["resourceSpans"][0]["scopeSpans"][0]["spans"][0]
        assert span["vendorExtension"] == {"anything": [1, 2]}

    def test_protobuf_unknown_fields_ignored_on_read(self):
        payload = (FIXTURES / "traces.pb").read_bytes()
        # Append an unknown field (field 99, varint 1); rows must be unaffected.
        with_unknown = payload + b"\xf8\x06\x01"
        rows = _read_pb(io.BytesIO(with_unknown), ExportTraceServiceRequest)
        assert rows == _read_pb(io.BytesIO(payload), ExportTraceServiceRequest)

    def test_item_key_selects_nested_envelope(self):
        document = {
            "data": {
                "resourceLogs": [
                    {"resource": {}, "scopeLogs": [{"scope": {}, "logRecords": [{"body": {"stringValue": "nested"}}]}]}
                ]
            }
        }
        source = OTLPJSONIterable.from_stream(io.StringIO(json.dumps(document)), item_key="data")
        rows = list(source)
        assert len(rows) == 1
        assert rows[0]["record"]["body"] == {"stringValue": "nested"}

    def test_item_key_missing_rejected(self):
        with pytest.raises(ValueError, match="item_key"):
            OTLPJSONIterable.from_stream(io.StringIO('{"other": {}}'), item_key="data")


class TestContentDetection:
    def _detect(self, payload: bytes):
        from iterable.helpers.content_detection import detect_file_type_from_content

        return detect_file_type_from_content(io.BytesIO(payload))

    def test_otlp_json_fixtures_detected(self):
        for name in ("traces", "logs", "metrics"):
            result = self._detect((FIXTURES / f"{name}.json").read_bytes())
            assert result is not None
            assert result[0] == "otlp-json", name
            assert result[1] >= 0.9

    def test_truncated_large_otlp_document_detected(self):
        payload = json.dumps(_large_trace_document()).encode("utf-8")
        assert len(payload) > 8192  # beyond the default detection peek
        result = self._detect(payload)
        assert result is not None
        assert result[0] == "otlp-json"

    def test_generic_json_not_detected_as_otlp(self):
        result = self._detect(b'{"name": "test", "values": [1, 2]}')
        assert result is not None
        assert result[0] == "json"

    def test_nested_lookalike_not_detected_as_otlp(self):
        payload = json.dumps({"outer": {"resourceSpans": [{"note": "not otlp"}]}}).encode("utf-8")
        result = self._detect(payload)
        assert result is not None
        assert result[0] == "json"

    def test_jsonl_not_detected_as_otlp(self):
        payload = b'{"a": 1}\n{"b": 2}\n{"c": 3}\n'
        result = self._detect(payload)
        assert result is not None
        assert result[0] == "jsonl"

    def test_compound_extension_detection(self, tmp_path):
        from iterable.helpers.detect import detect_file_type

        path = tmp_path / "export.otlp.json"
        path.write_text((FIXTURES / "traces.json").read_text())
        result = detect_file_type(str(path))
        assert result["success"]
        assert result["datatype"] is OTLPJSONIterable


class TestExplicitFormatSelection:
    def test_open_iterable_forces_otlp_json(self, tmp_path):
        from iterable import open_iterable

        path = tmp_path / "export.data"
        path.write_text((FIXTURES / "traces.json").read_text())
        with open_iterable(str(path), format="otlp-json") as source:
            rows = list(source)
        assert len(rows) == 3
        assert rows[0]["signal"] == "trace"

    def test_open_iterable_forces_otlp_protobuf(self, tmp_path):
        from iterable import open_iterable

        path = tmp_path / "export.bin"
        path.write_bytes((FIXTURES / "traces.pb").read_bytes())
        with open_iterable(
            str(path), format="otlp-protobuf", iterableargs={"message_class": ExportTraceServiceRequest}
        ) as source:
            rows = list(source)
        assert len(rows) == 3
        assert rows[0]["record"]["traceId"] == TRACE_ID

    def test_open_iterable_binary_via_compound_extension(self, tmp_path):
        from iterable import open_iterable

        path = tmp_path / "export.otlp.pb"
        path.write_bytes((FIXTURES / "logs.pb").read_bytes())
        with open_iterable(str(path), iterableargs={"message_class": ExportLogsServiceRequest}) as source:
            rows = list(source)
        assert len(rows) == 2


class TestIncrementalReading:
    def test_large_document_streams(self, tmp_path):
        path = tmp_path / "large.json"
        path.write_text(json.dumps(_large_trace_document()))
        source = OTLPJSONIterable.from_file(str(path))
        assert source._streaming, "large seekable documents must use incremental parsing"
        assert source._rows is None  # nothing materialized up front
        rows = list(source)
        assert len(rows) == 2000
        assert rows[0]["signal"] == "trace"
        assert rows[1999]["record"]["name"] == "span-199-9"

    def test_streaming_totals_and_reset(self, tmp_path):
        path = tmp_path / "large.json"
        path.write_text(json.dumps(_large_trace_document(envelopes=200, spans_per_envelope=2)))
        source = OTLPJSONIterable.from_file(str(path))
        assert source.totals() == 400
        first = source.read()
        assert first["record"]["name"] == "span-0-0"
        source.reset()
        assert source.read()["record"]["name"] == "span-0-0"

    def test_streaming_enforces_size_limit(self, tmp_path):
        path = tmp_path / "large.json"
        payload = json.dumps(_large_trace_document())
        path.write_text(payload)
        source = OTLPJSONIterable.from_file(str(path), max_message_bytes=len(payload) // 2)
        with pytest.raises(ValueError, match="max_message_bytes"):
            list(source)

    def test_streaming_malformed_tail_rejected(self, tmp_path):
        path = tmp_path / "large.json"
        payload = json.dumps(_large_trace_document())
        path.write_text(payload[:-5] + "<<<<<")
        source = OTLPJSONIterable.from_file(str(path))
        with pytest.raises(ValueError):
            list(source)

    def test_without_ijson_falls_back_to_bounded_parse(self, tmp_path, monkeypatch):
        monkeypatch.setattr(otlp_module, "ijson", None)
        path = tmp_path / "large.json"
        path.write_text(json.dumps(_large_trace_document(envelopes=200, spans_per_envelope=2)))
        source = OTLPJSONIterable.from_file(str(path))
        assert not source._streaming
        assert len(list(source)) == 400

    def test_bounded_memory_streaming(self, tmp_path):
        """A multi-MB export with many small envelopes streams below doc size."""
        path = tmp_path / "large.json"
        payload = json.dumps(_large_trace_document(envelopes=1200, spans_per_envelope=25))
        path.write_text(payload)
        doc_size = len(payload)
        assert doc_size > 3 * 1024 * 1024  # multi-MB document

        source = OTLPJSONIterable.from_file(str(path))
        assert source._streaming
        tracemalloc.start()
        count = 0
        for _ in source:
            count += 1
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert count == 30000
        assert peak < doc_size // 4, f"peak {peak} bytes vs document {doc_size} bytes"

    def test_read_bulk(self):
        source = OTLPJSONIterable.from_file(str(FIXTURES / "traces.json"))
        chunk = source.read_bulk(2)
        assert len(chunk) == 2
        assert len(source.read_bulk(10)) == 1
        assert source.read_bulk(10) == []


def test_otlp_json_envelope_and_round_trip():
    document = {
        "resourceSpans": [
            {
                "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "demo"}}]},
                "scopeSpans": [
                    {
                        "scope": {"name": "lib"},
                        "spans": [{"traceId": "ab" * 16, "spanId": "cd" * 8, "startTimeUnixNano": "1"}],
                    }
                ],
            }
        ]
    }
    source = OTLPJSONIterable.from_stream(io.StringIO(json.dumps(document)))
    row = source.read()
    assert row["signal"] == "trace"
    assert row["scope"]["name"] == "lib"

    output = io.StringIO()
    target = OTLPJSONIterable.from_stream(output, mode="w")
    target.write(row)
    target.flush()
    assert "resourceSpans" in output.getvalue()
