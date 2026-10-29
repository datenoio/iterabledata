"""gzip codec backends: ISA-L when installed and requested, zlib otherwise; output stays gzip."""

import gzip
import io

import pytest

from iterable.codecs import gzipcodec
from iterable.codecs.gzipcodec import GZIPCodec
from iterable.helpers.detect import open_iterable

ROWS = [{"id": i, "text": f"row {i} " * 5} for i in range(2000)]


def _write(path, **codecargs):
    with open_iterable(str(path), mode="w", codecargs=codecargs) as dest:
        dest.write_bulk(ROWS)


def _read_lines(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return f.read().splitlines()


def _backend_of(codec):
    return type(codec.fileobj()).__module__.split(".")[0]


@pytest.mark.parametrize(
    "codecargs",
    [{}, {"profile": "fast"}, {"compression_level": 1}, {"profile": "max"}, {"backend": "stdlib", "profile": "fast"}],
)
def test_output_is_standard_gzip(tmp_path, codecargs):
    path = tmp_path / "out.jsonl.gz"
    _write(path, **codecargs)
    lines = _read_lines(path)
    assert len(lines) == len(ROWS)
    assert lines[1] == '{"id":1,"text":"row 1 row 1 row 1 row 1 row 1 "}'


def test_backend_choice_without_isal(tmp_path, monkeypatch):
    monkeypatch.setattr(gzipcodec, "isal_available", lambda: False)
    codec = GZIPCodec(filename=str(tmp_path / "a.gz"), mode="w", options={"profile": "fast"})
    codec.open()
    assert _backend_of(codec) == "gzip"
    codec.close()
    with pytest.raises(ImportError, match="iterabledata\\[fast\\]"):
        GZIPCodec(filename=str(tmp_path / "b.gz"), mode="w", options={"backend": "isal"}).open()


def test_unknown_backend_is_rejected():
    with pytest.raises(ValueError, match="Unsupported gzip backend"):
        GZIPCodec(fileobj=io.BytesIO(), mode="w", options={"backend": "zlib-ng"})


@pytest.mark.skipif(not gzipcodec.isal_available(), reason="isal is not installed")
class TestWithIsal:
    def _codec(self, tmp_path, mode="w", **options):
        codec = GZIPCodec(filename=str(tmp_path / "x.gz"), mode=mode, options=options)
        codec.open()
        return codec

    def test_auto_uses_isal_only_where_ratio_matches_zlib(self, tmp_path):
        for options, expected in [
            ({"profile": "fast"}, "isal"),
            ({"compression_level": 2}, "isal"),
            ({}, "gzip"),
            ({"profile": "max"}, "gzip"),
            ({"backend": "stdlib", "compression_level": 1}, "gzip"),
            ({"backend": "isal", "profile": "max"}, "isal"),
        ]:
            codec = self._codec(tmp_path, **options)
            assert _backend_of(codec) == expected, options
            codec.close()

    def test_reads_use_isal_only_on_request(self, tmp_path):
        path = tmp_path / "x.gz"
        path.write_bytes(gzip.compress(b"abc\n"))
        reader = self._codec(tmp_path, mode="r")
        assert _backend_of(reader) == "gzip"
        reader.close()
        reader = self._codec(tmp_path, mode="r", backend="isal")
        assert _backend_of(reader) == "isal"
        assert reader.fileobj().read() == b"abc\n"
        reader.close()

    def test_threaded_writer_on_a_stream(self):
        buffer = io.BytesIO()
        codec = GZIPCodec(fileobj=buffer, mode="w", options={"profile": "fast"})
        codec.open()
        codec.fileobj().write(b"hello\n" * 1000)
        codec.close()
        assert gzip.decompress(buffer.getvalue()) == b"hello\n" * 1000
