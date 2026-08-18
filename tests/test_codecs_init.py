"""Tests for iterable/codecs/__init__.py"""

from iterable.codecs import (
    BZIP2Codec,
    GZIPCodec,
    LZMACodec,
    RAWCodec,
    ZIPCodec,
)


class TestCodecsInit:
    """Test codecs __init__ module"""

    def test_core_codecs_available(self):
        """Test that core codecs are always available"""
        assert BZIP2Codec is not None
        assert GZIPCodec is not None
        assert LZMACodec is not None
        assert RAWCodec is not None
        assert ZIPCodec is not None

    def test_optional_codecs_conditional(self):
        """Test that optional codecs are conditionally imported"""
        from iterable.codecs import BrotliCodec, LZ4Codec, LZOCodec, SnappyCodec, SZipCodec, ZSTDCodec

        for codec_cls in (BrotliCodec, LZ4Codec, LZOCodec, SnappyCodec, ZSTDCodec, SZipCodec):
            assert codec_cls is None or hasattr(codec_cls, "fileexts")

    def test_gzip_codec_import(self):
        """Test GZIPCodec can be imported"""
        from iterable.codecs import GZIPCodec

        assert GZIPCodec is not None
        assert GZIPCodec.fileexts() == ["gz"]

    def test_bz2_codec_import(self):
        """Test BZIP2Codec can be imported"""
        from iterable.codecs import BZIP2Codec

        assert BZIP2Codec is not None
        assert BZIP2Codec.fileexts() == ["bz2"]

    def test_lzma_codec_import(self):
        """Test LZMACodec can be imported"""
        from iterable.codecs import LZMACodec

        assert LZMACodec is not None
        assert "xz" in LZMACodec.fileexts() or "lzma" in LZMACodec.fileexts()

    def test_raw_codec_import(self):
        """Test RAWCodec can be imported"""
        from iterable.codecs import RAWCodec

        assert RAWCodec is not None

    def test_zip_codec_import(self):
        """Test ZIPCodec can be imported"""
        from iterable.codecs import ZIPCodec

        assert ZIPCodec is not None
        assert ZIPCodec.fileexts() == ["zip"]
