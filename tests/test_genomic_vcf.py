"""Tests for genomic VCF/BCF support and .vcf content disambiguation."""

import io

import pytest

from iterable.helpers.content_detection import detect_file_type_from_content

GENOMIC_FIXTURE = "fixtures/sample.genomic.vcf"
VCARD_FIXTURE = "fixtures/sample.vcard.vcf"


class TestVCFContentDisambiguation:
    """The shared .vcf extension is resolved by content, not extension alone."""

    def test_genomic_content_detected_as_genomic_vcf(self):
        with open(GENOMIC_FIXTURE, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        fmt, _confidence, _method = result
        assert fmt == "genomic_vcf"

    def test_vcard_content_detected_as_vcf(self):
        with open(VCARD_FIXTURE, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        fmt, _confidence, _method = result
        assert fmt == "vcf"

    def test_detect_file_type_prefers_content_for_genomic_vcf(self):
        from iterable.datatypes.genomic_vcf import GenomicVCFIterable
        from iterable.helpers.detect import detect_file_type

        with open(GENOMIC_FIXTURE, "rb") as f:
            result = detect_file_type(GENOMIC_FIXTURE, fileobj=f)
        assert result["success"]
        assert result["datatype"] is GenomicVCFIterable

    def test_detect_file_type_keeps_vcard_for_vcard_content(self):
        from iterable.datatypes.vcf import VCFIterable
        from iterable.helpers.detect import detect_file_type

        with open(VCARD_FIXTURE, "rb") as f:
            result = detect_file_type(VCARD_FIXTURE, fileobj=f)
        assert result["success"]
        assert result["datatype"] is VCFIterable


class TestGenomicVCFMissingBackend:
    def test_import_error_names_bio_extra(self, monkeypatch):
        import iterable.datatypes.genomic_vcf as mod

        monkeypatch.setattr(mod, "HAS_PYSAM", False)
        with pytest.raises(ImportError, match=r"iterabledata\[bio\]"):
            mod.GenomicVCFIterable("fixtures/sample.genomic.vcf")


pysam = pytest.importorskip("pysam", reason="pysam is required for genomic VCF support")


class TestGenomicVCFReading:
    def test_reads_variants(self):
        from iterable.datatypes.genomic_vcf import GenomicVCFIterable

        with GenomicVCFIterable(GENOMIC_FIXTURE) as source:
            rows = list(source)

        assert len(rows) == 5
        first = rows[0]
        assert first["CHROM"] == "1"
        assert first["POS"] == 14370
        assert first["ID"] == "rs6054257"
        assert first["REF"] == "G"
        assert first["ALT"] == ["A"]
        assert first["INFO"]["DP"] == 14
        assert "SAMPLE1" in first["SAMPLES"]

    def test_open_iterable_routes_to_genomic_vcf(self):
        from iterable.datatypes.genomic_vcf import GenomicVCFIterable
        from iterable.helpers.detect import open_iterable

        with open_iterable(GENOMIC_FIXTURE) as source:
            assert isinstance(source, GenomicVCFIterable)
            first = source.read()
        assert first["CHROM"] == "1"
        assert first["POS"] == 14370

    def test_is_streaming(self):
        from iterable.datatypes.genomic_vcf import GenomicVCFIterable

        with GenomicVCFIterable(GENOMIC_FIXTURE) as source:
            assert source.is_streaming()

    def test_reset_round_trip(self):
        from iterable.datatypes.genomic_vcf import GenomicVCFIterable

        with GenomicVCFIterable(GENOMIC_FIXTURE) as source:
            first = source.read()
            source.reset()
            assert source.read() == first

    def test_stream_not_supported(self):
        from iterable.datatypes.genomic_vcf import GenomicVCFIterable

        with pytest.raises(ValueError, match="requires a filename"):
            GenomicVCFIterable(stream=io.BytesIO(b"##fileformat=VCFv4.2\n"))
