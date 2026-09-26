"""Behavior-pinning tests for detect_file_type (complexity refactor).

Pins the observable behavior of ``iterable.helpers.detect.detect_file_type``
before/after the behavior-preserving decomposition: filename-based detection
(single extension, extension+codec, compound profile suffixes), result shape
and defaults, error paths, ambiguous-extension content override, and the
content-detection fallback when filename detection fails.
"""

import pytest

from iterable.codecs import BZIP2Codec, GZIPCodec, LZMACodec
from iterable.datatypes import CSVIterable, JSONIterable
from iterable.datatypes.vcf import VCFIterable
from iterable.helpers.detect import detect_file_type

try:
    from iterable.codecs import ZSTDCodec
except (ImportError, NameError):
    ZSTDCodec = None

GENOMIC_FIXTURE = "fixtures/sample.genomic.vcf"
VCARD_FIXTURE = "fixtures/sample.vcard.vcf"


def _assert_failed(result):
    assert result["success"] is False
    assert result["datatype"] is None
    assert result["codec"] is None
    assert result["confidence"] == 0.0
    assert result["detection_method"] == "none"


class TestResultShapeAndErrors:
    def test_empty_filename_raises(self):
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            detect_file_type("")

    def test_result_keys(self):
        result = detect_file_type("fixtures/ru_utf8_comma.csv")
        assert set(result.keys()) == {"filename", "success", "codec", "datatype", "confidence", "detection_method"}
        assert result["filename"] == "fixtures/ru_utf8_comma.csv"

    def test_no_extension_fails(self):
        _assert_failed(detect_file_type("noext"))

    def test_unknown_extension_fails(self):
        _assert_failed(detect_file_type("test.unknown"))

    def test_codec_only_filename_fails(self):
        """A bare codec extension is not a datatype; filename detection fails."""
        _assert_failed(detect_file_type("file.gz"))

    def test_unknown_trailing_extension_fails(self):
        """'a.csv.unknown': 'unknown' is neither a codec nor a format."""
        _assert_failed(detect_file_type("a.csv.unknown"))


class TestFilenameDetection:
    def test_simple_extension(self):
        result = detect_file_type("fixtures/ru_utf8_comma.csv")
        assert result["success"] is True
        assert result["datatype"] == CSVIterable
        assert result["codec"] is None
        assert result["confidence"] == 1.0
        assert result["detection_method"] == "filename"

    def test_extension_case_insensitive(self):
        result = detect_file_type("TEST.CSV")
        assert result["success"] is True
        assert result["datatype"] == CSVIterable

    def test_multi_dot_filename_detects_last_extension(self):
        result = detect_file_type("a.b.c.csv")
        assert result["success"] is True
        assert result["datatype"] == CSVIterable
        assert result["codec"] is None

    def test_extension_with_gzip_codec(self):
        result = detect_file_type("fixtures/2cols6rows.csv.gz")
        assert result["datatype"] == CSVIterable
        assert result["codec"] == GZIPCodec
        assert result["confidence"] == 1.0
        assert result["detection_method"] == "filename"

    def test_extension_with_bzip2_codec(self):
        result = detect_file_type("fixtures/2cols6rows.csv.bz2")
        assert result["datatype"] == CSVIterable
        assert result["codec"] == BZIP2Codec

    def test_extension_with_lzma_codec(self):
        result = detect_file_type("fixtures/2cols6rows.csv.xz")
        assert result["datatype"] == CSVIterable
        assert result["codec"] == LZMACodec

    def test_extension_with_zstd_codec(self):
        if ZSTDCodec is None:
            pytest.skip("ZSTDCodec not available")
        result = detect_file_type("fixtures/2cols6rows.csv.zst")
        assert result["datatype"] == CSVIterable
        assert result["codec"] == ZSTDCodec

    def test_json_with_gzip_codec(self):
        result = detect_file_type("a.json.gz")
        assert result["datatype"] == JSONIterable
        assert result["codec"] == GZIPCodec


class TestCompoundProfiles:
    """Compound profile suffixes resolve before the generic last-dot lookup."""

    def test_otlp_json(self):
        from iterable.datatypes.otlp import OTLPJSONIterable

        result = detect_file_type("x.otlp.json")
        assert result["datatype"] == OTLPJSONIterable
        assert result["codec"] is None
        assert result["confidence"] == 1.0
        assert result["detection_method"] == "filename"

    def test_otlp_json_with_codec(self):
        from iterable.datatypes.otlp import OTLPJSONIterable

        result = detect_file_type("x.otlp.json.gz")
        assert result["datatype"] == OTLPJSONIterable
        assert result["codec"] == GZIPCodec

    def test_otlp_protobuf_suffixes(self):
        pytest.importorskip("google.protobuf", reason="protobuf extra not installed")
        pytest.importorskip("opentelemetry.proto", reason="opentelemetry-proto not installed")
        from iterable.datatypes.otlp import OTLPProtobufIterable

        assert detect_file_type("x.otlp.pb")["datatype"] == OTLPProtobufIterable
        assert detect_file_type("x.otlp.protobuf")["datatype"] == OTLPProtobufIterable

    def test_geoparquet(self):
        pytest.importorskip("pyarrow", reason="pyarrow is required for GeoParquet support")
        from iterable.datatypes.geoparquet import GeoParquetIterable

        result = detect_file_type("x.geoparquet")
        assert result["datatype"] == GeoParquetIterable

    def test_iati_xml(self):
        from iterable.datatypes.iati import IATIIterable

        result = detect_file_type("x.iati.xml")
        assert result["datatype"] == IATIIterable


class TestAmbiguousExtension:
    def test_vcf_without_fileobj_uses_extension(self):
        """Without content, the .vcf extension maps to the vCard datatype."""
        result = detect_file_type("x.vcf")
        assert result["success"] is True
        assert result["datatype"] is VCFIterable
        assert result["confidence"] == 1.0
        assert result["detection_method"] == "filename"

    def test_vcf_genomic_content_overrides(self):
        from iterable.datatypes.genomic_vcf import GenomicVCFIterable

        with open(GENOMIC_FIXTURE, "rb") as f:
            result = detect_file_type(GENOMIC_FIXTURE, fileobj=f)
        assert result["success"] is True
        assert result["datatype"] is GenomicVCFIterable

    def test_vcf_vcard_content_kept(self):
        with open(VCARD_FIXTURE, "rb") as f:
            result = detect_file_type(VCARD_FIXTURE, fileobj=f)
        assert result["success"] is True
        assert result["datatype"] is VCFIterable

    def test_vcf_content_override_confidence_and_method(self):
        """The content verdict replaces confidence/method for ambiguous extensions."""
        with open(GENOMIC_FIXTURE, "rb") as f:
            result = detect_file_type(GENOMIC_FIXTURE, fileobj=f)
        assert result["confidence"] >= 0.95
        assert result["detection_method"] == "magic_number"


class TestContentFallback:
    def test_content_fallback_json(self, tmp_path):
        json_file = tmp_path / "data"
        json_file.write_text('{"name": "test"}')
        with open(json_file, "rb") as f:
            result = detect_file_type(str(json_file), fileobj=f)
        assert result["success"] is True
        assert result["datatype"] == JSONIterable
        assert 0.8 <= result["confidence"] <= 1.0
        assert result["detection_method"] == "heuristic"

    def test_content_fallback_csv(self, tmp_path):
        data_file = tmp_path / "data.unknownext"
        data_file.write_text("id,name\n1,test\n2,test2\n")
        with open(data_file, "rb") as f:
            result = detect_file_type(str(data_file), fileobj=f)
        assert result["success"] is True
        assert result["datatype"] == CSVIterable
        assert result["detection_method"] == "heuristic"

    def test_content_fallback_no_match(self, tmp_path):
        """Undetectable content leaves the failed filename result untouched."""
        binary_file = tmp_path / "data.unknownext"
        binary_file.write_bytes(b"\x00\x01\x02\x03" * 100)
        with open(binary_file, "rb") as f:
            result = detect_file_type(str(binary_file), fileobj=f)
        _assert_failed(result)

    def test_filename_priority_over_content(self, tmp_path):
        """Filename detection wins for non-ambiguous extensions, even with a fileobj."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text('{"name": "test"}')  # JSON-like content, CSV filename
        with open(csv_file, "rb") as f:
            result = detect_file_type(str(csv_file), fileobj=f)
        assert result["datatype"] == CSVIterable
        assert result["confidence"] == 1.0
        assert result["detection_method"] == "filename"


class TestDebugParameter:
    def test_debug_flag_does_not_change_result(self):
        plain = detect_file_type("fixtures/ru_utf8_comma.csv")
        debugged = detect_file_type("fixtures/ru_utf8_comma.csv", debug=True)
        assert plain == debugged

    def test_debug_flag_failure_result(self):
        _assert_failed(detect_file_type("test.unknown", debug=True))
