"""Tests for GeoJSON Text Sequences (RFC 8142)."""

import json

from iterable.datatypes import GeoJSONSeqIterable
from iterable.helpers.detect import detect_file_type, open_iterable

NAMES = ["John", "Mary", "Michael", "Anna", "Orban", "Lucy"]


class TestGeoJSONSeq:
    def test_id(self):
        assert GeoJSONSeqIterable.id() == "geojsonseq"

    def test_is_streaming(self):
        iterable = GeoJSONSeqIterable("fixtures/2cols6rows.geojsonl")
        assert iterable.is_streaming() is True
        iterable.close()

    def test_read_features_line_by_line(self):
        with open_iterable("fixtures/2cols6rows.geojsonl") as source:
            rows = list(source)
        assert len(rows) == 6
        for n, row in enumerate(rows):
            assert row["type"] == "Feature"
            assert row["properties"]["id"] == str(n + 1)
            assert row["properties"]["name"] == NAMES[n]

    def test_read_with_record_separator(self):
        """RFC 8142 \\x1e-prefixed sequences parse correctly."""
        with open_iterable("fixtures/2cols6rows_rs.geojsons") as source:
            rows = list(source)
        assert len(rows) == 6
        assert rows[0]["properties"]["name"] == "John"
        assert rows[-1]["properties"]["name"] == "Lucy"

    def test_read_bulk(self):
        iterable = GeoJSONSeqIterable("fixtures/2cols6rows.geojsonl")
        chunk = iterable.read_bulk(4)
        assert len(chunk) == 4
        rest = iterable.read_bulk(10)
        assert len(rest) == 2
        assert iterable.read_bulk(10) == []
        iterable.close()

    def test_read_bulk_with_record_separator(self):
        iterable = GeoJSONSeqIterable("fixtures/2cols6rows_rs.geojsons")
        chunk = iterable.read_bulk(10)
        assert len(chunk) == 6
        assert chunk[0]["type"] == "Feature"
        iterable.close()

    def test_reset(self):
        iterable = GeoJSONSeqIterable("fixtures/2cols6rows.geojsonl")
        first = iterable.read()
        iterable.reset()
        again = iterable.read()
        assert first == again
        iterable.close()

    def test_write_one_feature_per_line(self, tmp_path):
        features = [
            {"type": "Feature", "properties": {"id": str(i)}, "geometry": {"type": "Point", "coordinates": [i, i]}}
            for i in range(3)
        ]
        out = tmp_path / "out.geojsonl"
        with open_iterable(str(out), mode="w") as dest:
            dest.write_bulk(features)

        lines = out.read_text().strip().split("\n")
        assert len(lines) == 3
        for line in lines:
            assert json.loads(line)["type"] == "Feature"

    def test_write_read_round_trip(self, tmp_path):
        with open_iterable("fixtures/2cols6rows.geojsonl") as source:
            rows = list(source)

        out = tmp_path / "roundtrip.geojsonl"
        with open_iterable(str(out), mode="w") as dest:
            dest.write_bulk(rows)

        with open_iterable(str(out)) as reread:
            roundtrip = list(reread)

        assert roundtrip == rows


class TestGeoJSONSeqDetection:
    def test_detect_by_extension_geojsonl(self):
        result = detect_file_type("fixtures/2cols6rows.geojsonl")
        assert result["success"]
        assert result["datatype"] == GeoJSONSeqIterable

    def test_detect_by_extension_geojsons(self):
        result = detect_file_type("fixtures/2cols6rows_rs.geojsons")
        assert result["success"]
        assert result["datatype"] == GeoJSONSeqIterable

    def test_detect_by_content(self, tmp_path):
        from iterable.helpers.content_detection import detect_file_type_from_content

        path = tmp_path / "noext"
        feature = {"type": "Feature", "properties": {"id": "1"}, "geometry": None}
        path.write_text("\n".join([json.dumps(feature)] * 4) + "\n")
        with open(path, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        assert result[0] == "geojsonseq"
        assert result[2] == "heuristic"

    def test_content_detection_does_not_claim_plain_jsonl(self, tmp_path):
        from iterable.helpers.content_detection import detect_file_type_from_content

        path = tmp_path / "noext"
        path.write_text('{"id": 1}\n{"id": 2}\n{"id": 3}\n{"id": 4}\n')
        with open(path, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        assert result[0] == "jsonl"
