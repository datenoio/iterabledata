import pytest
from fixdata import FIXTURES

pytest.importorskip("snappy", reason="python-snappy is required for Snappy support")

from iterable.codecs import SnappyCodec  # noqa: E402
from iterable.datatypes import CSVIterable  # noqa: E402


class TestSnappy:
    def test_fileexts(self):
        assert SnappyCodec.fileexts() == ["snappy", "sz"]

    def test_openclose(self):
        codecobj = SnappyCodec("fixtures/2cols6rows.csv.snappy", mode="r")
        iterable = CSVIterable(codec=codecobj)
        iterable.close()

    def test_parsesimple_readone(self):
        codecobj = SnappyCodec("fixtures/2cols6rows.csv.snappy", mode="r")
        iterable = CSVIterable(codec=codecobj)
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.close()

    def test_parsesimple_reset(self):
        codecobj = SnappyCodec("fixtures/2cols6rows.csv.snappy", mode="r")
        iterable = CSVIterable(codec=codecobj)
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = iterable.read()
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_next(self):
        codecobj = SnappyCodec("fixtures/2cols6rows.csv.snappy", mode="r")
        iterable = CSVIterable(codec=codecobj)
        row = next(iterable)
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = next(iterable)
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_count(self):
        codecobj = SnappyCodec("fixtures/2cols6rows.csv.snappy", mode="r")
        iterable = CSVIterable(codec=codecobj)
        n = 0
        for _row in iterable:
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_parsesimple_iterateall(self):
        codecobj = SnappyCodec("fixtures/2cols6rows.csv.snappy", mode="r")
        iterable = CSVIterable(codec=codecobj)
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_write_read(self):
        codecobj = SnappyCodec("testdata/2cols6rows_test.csv.snappy", mode="w")
        iterable = CSVIterable(codec=codecobj, mode="w", keys=["id", "name"])
        for row in FIXTURES:
            iterable.write(row)
        iterable.close()
        codecobj = SnappyCodec("fixtures/2cols6rows.csv.snappy", mode="r")
        iterable = CSVIterable(codec=codecobj)
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_roundtrip_jsonl(self, tmp_path):
        from iterable.helpers.detect import open_iterable

        path = str(tmp_path / "roundtrip.jsonl.snappy")
        with open_iterable(path, mode="w") as dest:
            for row in FIXTURES:
                dest.write(row)
        with open_iterable(path) as source:
            rows = list(source)
        assert rows == FIXTURES

    def test_roundtrip_own_output(self, tmp_path):
        """Files written by SnappyCodec are read back correctly (framed format)."""
        path = str(tmp_path / "roundtrip.csv.snappy")
        codecobj = SnappyCodec(path, mode="w")
        iterable = CSVIterable(codec=codecobj, mode="w", keys=["id", "name"])
        for row in FIXTURES:
            iterable.write(row)
        iterable.close()

        codecobj = SnappyCodec(path, mode="r")
        iterable = CSVIterable(codec=codecobj)
        rows = list(iterable)
        iterable.close()
        assert rows == FIXTURES


class TestSnappyStreaming:
    """Framed snappy files must be processed lazily in bounded memory."""

    ROWS = 200_000  # ~ tens of MB of plaintext

    def _write_large(self, path):
        import snappy as _snappy

        compressor = _snappy.StreamCompressor()
        with open(path, "wb") as f:
            f.write(compressor.compress(b"id,name\r\n"))
            for i in range(self.ROWS):
                f.write(compressor.compress(f"{i},name-{i}-{'x' * 100}\r\n".encode()))

    def test_framed_read_is_lazy_wrapper(self, tmp_path):
        import io

        path = str(tmp_path / "large.csv.snappy")
        self._write_large(path)
        codecobj = SnappyCodec(path, mode="r")
        fobj = codecobj.open()
        assert isinstance(fobj, io.BufferedReader), "framed snappy should stream, not buffer into BytesIO"
        codecobj.close()

    def test_large_roundtrip_bounded_memory(self, tmp_path):
        import tracemalloc

        path = str(tmp_path / "large.csv.snappy")
        self._write_large(path)
        uncompressed_size = self.ROWS * 110

        codecobj = SnappyCodec(path, mode="r")
        iterable = CSVIterable(codec=codecobj)
        tracemalloc.start()
        n = 0
        for row in iterable:
            assert row["id"] == str(n)
            n += 1
        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        iterable.close()

        assert n == self.ROWS
        # Streaming keeps peak allocation far below the uncompressed payload.
        assert peak < uncompressed_size / 4, f"peak {peak} suggests full-buffer decompression"
