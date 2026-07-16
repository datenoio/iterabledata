import io
import json

from iterable.datatypes.otlp import OTLPJSONIterable

DOCUMENT = {
    "resourceSpans": [
        {
            "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "demo"}}]},
            "scopeSpans": [{"scope": {"name": "lib"}, "spans": [{"traceId": "abc", "startTimeUnixNano": "1"}]}],
        }
    ]
}


def test_otlp_json_envelope_and_round_trip():
    source = OTLPJSONIterable.from_stream(io.StringIO(json.dumps(DOCUMENT)))
    row = source.read()
    assert row["signal"] == "traces"
    assert row["scope"]["name"] == "lib"

    output = io.StringIO()
    target = OTLPJSONIterable.from_stream(output, mode="w")
    target.write(row)
    assert "resourceSpans" in output.getvalue()
