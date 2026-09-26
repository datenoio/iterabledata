"""Behavior-pinning tests for detect_file_type_from_content (complexity refactor).

Pins the observable behavior of
``iterable.helpers.content_detection.detect_file_type_from_content``
before/after the behavior-preserving decomposition: detection order (magic
prefix -> TAR ustar -> Paimon footer -> VCF -> GeoJSONSeq -> OTLP -> JSON ->
delimited -> JSONL-count), exact (format_id, confidence, method) tuples, stream
position restoration, and the None fall-through paths.
"""

import io

from iterable.helpers.content_detection import detect_file_type_from_content as det


def _detect(data: bytes):
    return det(io.BytesIO(data))


class TestStreamContract:
    def test_position_restored(self):
        f = io.BytesIO(b'{"name": "test"}')
        f.read(1)  # move away from 0
        det(f)
        assert f.tell() == 1

    def test_position_restored_on_no_match(self):
        f = io.BytesIO(b"\x00\x01\x02\x03" * 100)
        det(f)
        assert f.tell() == 0

    def test_empty_peek_returns_none(self):
        assert _detect(b"") is None

    def test_text_stream_returns_none(self):
        """A text (str) stream violates the binary contract; caught -> None."""
        assert det(io.StringIO('{"a": 1}')) is None


class TestMagicNumbers:
    def test_parquet(self):
        assert _detect(b"PAR1" + b"\x00" * 100) == ("parquet", 0.99, "magic_number")

    def test_orc(self):
        assert _detect(b"ORC" + b"\x00" * 100) == ("orc", 0.99, "magic_number")

    def test_arrow(self):
        assert _detect(b"ARROW1" + b"\x00" * 50) == ("arrow", 0.99, "magic_number")

    def test_tar_ustar_at_offset_257(self):
        data = b"\x00" * 257 + b"ustar" + b"\x00" * 300
        assert _detect(data) == ("tar", 0.95, "magic_number")

    def test_paimon_row_footer(self):
        footer = bytearray(32)
        footer[-4:] = b"ROWS"
        footer[25:28] = b"\x00\x00\x00"
        assert _detect(b"\x00" * 64 + bytes(footer)) == ("paimon_row", 0.95, "magic_number")

    def test_paimon_mosaic_footer(self):
        footer = bytearray(32)
        footer[-4:] = b"MOSA"
        assert _detect(b"\x00" * 64 + bytes(footer)) == ("paimon_mosaic", 0.95, "magic_number")

    def test_file_smaller_than_footer_not_paimon(self):
        assert _detect(b"ROWS") is None


class TestTextHeuristics:
    def test_json_object(self):
        assert _detect(b'{"name": "test", "v": 1}') == ("json", 0.90, "heuristic")

    def test_json_array(self):
        assert _detect(b'[{"a":1}]') == ("json", 0.90, "heuristic")

    def test_jsonl_via_first_line_fallback(self):
        """Multi-line JSON docs fail full parse; a valid first line -> jsonl 0.80."""
        assert _detect(b'{"a":1}\n{"a":2}\n{"a":3}\n') == ("jsonl", 0.80, "heuristic")

    def test_jsonl_truncated_second_line(self):
        assert _detect(b'{"a":1}\n{"a":2') == ("jsonl", 0.80, "heuristic")

    def test_jsonl_count_branch_three_lines(self):
        """Lines that do not start with {/[ reach the jsonl-count branch."""
        assert _detect(b"1\n2\n3\n") == ("jsonl", 0.85, "heuristic")

    def test_jsonl_count_branch_confidence_capped(self):
        assert _detect(b"1\n2\n3\n4\n5\n6\n") == ("jsonl", 0.90, "heuristic")

    def test_truncated_json_no_match(self):
        assert _detect(b'{"name": "test", "v": ') is None

    def test_junk_prefix_no_match(self):
        assert _detect(b"XXXX" + b'{"name": "test"}') is None

    def test_plain_text_no_match(self):
        assert _detect(b"hello world this is plain text\n" * 5) is None

    def test_binary_no_match(self):
        assert _detect(b"\x00\x01\x02\x03" * 100) is None


class TestDelimitedHeuristics:
    def test_csv_equal_counts(self):
        assert _detect(b"id,name\n1,x\n2,y\n") == ("csv", 0.85, "heuristic")

    def test_csv_counts_within_two(self):
        assert _detect(b"id,name\n1,x,y\n2,z\n") == ("csv", 0.75, "heuristic")

    def test_tsv(self):
        assert _detect(b"id\tname\n1\tx\n2\ty\n") == ("tsv", 0.85, "heuristic")

    def test_pipe_psv(self):
        assert _detect(b"id|name\n1|x\n2|y\n") == ("psv", 0.85, "heuristic")

    def test_semicolon_maps_to_psv(self):
        """Quirk: ';' delimiters are reported as psv, not ssv."""
        assert _detect(b"id;name\n1;x\n2;y\n") == ("psv", 0.85, "heuristic")


class TestSpecializedTextFormats:
    def test_genomic_vcf(self):
        assert _detect(b"##fileformat=VCFv4.2\n#CHROM\tPOS\n") == ("genomic_vcf", 0.98, "magic_number")

    def test_vcard(self):
        assert _detect(b"BEGIN:VCARD\nVERSION:3.0\nEND:VCARD") == ("vcf", 0.95, "heuristic")

    def test_geojsonseq(self):
        line = b'{"type":"Feature","geometry":null,"properties":{}}'
        assert _detect(b"\x1e" + line + b"\n\x1e" + line + b"\n") == ("geojsonseq", 0.78, "heuristic")

    def test_otlp_json(self):
        assert _detect(b'{"resourceSpans": []}') == ("otlp-json", 0.95, "heuristic")

    def test_generic_json_not_otlp(self):
        """Nested resourceSpans lookalikes stay plain json."""
        assert _detect(b'{"outer": {"resourceSpans": []}}') == ("json", 0.90, "heuristic")


class TestDetectionOrder:
    def test_magic_beats_text_heuristics(self):
        """A magic match returns before any text heuristic is attempted."""
        result = _detect(b"PAR1" + b'{"a":1}\n' * 10)
        assert result == ("parquet", 0.99, "magic_number")

    def test_vcf_beats_delimiter_heuristics(self):
        """VCF check runs before the delimiter heuristic even with commas."""
        result = _detect(b"##fileformat=VCFv4.2\n#CHROM,POS,ID\n1,2,3\n")
        assert result == ("genomic_vcf", 0.98, "magic_number")

    def test_json_object_beats_delimiters(self):
        """A parseable JSON object wins over the delimiter heuristic."""
        result = _detect(b'{"a": "b,c"}')
        assert result == ("json", 0.90, "heuristic")
