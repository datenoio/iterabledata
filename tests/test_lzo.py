import pytest
from fixdata import FIXTURES

from iterable.codecs import LZOCodec
from iterable.datatypes import CSVIterable

# Check if LZO is available
try:
    import lzo  # noqa: F401

    LZO_AVAILABLE = True
except ImportError:
    LZO_AVAILABLE = False


@pytest.mark.skipif(not LZO_AVAILABLE, reason="python-lzo library not available")
class TestLZO:
    def test_fileexts(self):
        assert LZOCodec.fileexts() == ["lzo", "lzop"]

    def test_openclose(self):
        codecobj = LZOCodec("fixtures/2cols6rows.csv.lzo", mode="r")
        iterable = CSVIterable(codec=codecobj)
        iterable.close()

    def test_parsesimple_readone(self):
        codecobj = LZOCodec("fixtures/2cols6rows.csv.lzo", mode="r")
        iterable = CSVIterable(codec=codecobj)
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.close()

    def test_parsesimple_reset(self):
        codecobj = LZOCodec("fixtures/2cols6rows.csv.lzo", mode="r")
        iterable = CSVIterable(codec=codecobj)
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = iterable.read()
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_next(self):
        codecobj = LZOCodec("fixtures/2cols6rows.csv.lzo", mode="r")
        iterable = CSVIterable(codec=codecobj)
        row = next(iterable)
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = next(iterable)
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_count(self):
        codecobj = LZOCodec("fixtures/2cols6rows.csv.lzo", mode="r")
        iterable = CSVIterable(codec=codecobj)
        n = 0
        for _row in iterable:
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_parsesimple_iterateall(self):
        codecobj = LZOCodec("fixtures/2cols6rows.csv.lzo", mode="r")
        iterable = CSVIterable(codec=codecobj)
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_write_read(self):
        codecobj = LZOCodec("testdata/2cols6rows_test.csv.lzo", mode="w")
        iterable = CSVIterable(codec=codecobj, mode="w", keys=["id", "name"])
        for row in FIXTURES:
            iterable.write(row)
        iterable.close()
        codecobj = LZOCodec("fixtures/2cols6rows.csv.lzo", mode="r")
        iterable = CSVIterable(codec=codecobj)
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_roundtrip_jsonl(self, tmp_path):
        from iterable.helpers.detect import open_iterable

        path = str(tmp_path / "roundtrip.jsonl.lzo")
        with open_iterable(path, mode="w") as dest:
            for row in FIXTURES:
                dest.write(row)
        with open_iterable(path) as source:
            rows = list(source)
        assert rows == FIXTURES

    def test_roundtrip_own_output(self, tmp_path):
        """Files written by LZOCodec are read back correctly (block-framed format)."""
        path = str(tmp_path / "roundtrip.csv.lzo")
        codecobj = LZOCodec(path, mode="w")
        iterable = CSVIterable(codec=codecobj, mode="w", keys=["id", "name"])
        for row in FIXTURES:
            iterable.write(row)
        iterable.close()

        codecobj = LZOCodec(path, mode="r")
        iterable = CSVIterable(codec=codecobj)
        rows = list(iterable)
        iterable.close()
        assert rows == FIXTURES

    def test_legacy_oneshot_blob_still_readable(self, tmp_path):
        """Raw lzo.compress blobs from earlier codec versions still read via fallback."""
        import lzo as _lzo

        path = str(tmp_path / "legacy.csv.lzo")
        with open("fixtures/2cols6rows.csv", "rb") as f:
            plain = f.read()
        with open(path, "wb") as f:
            f.write(_lzo.compress(plain, 1))

        codecobj = LZOCodec(path, mode="r")
        iterable = CSVIterable(codec=codecobj)
        rows = list(iterable)
        iterable.close()
        assert rows == FIXTURES


@pytest.mark.skipif(not LZO_AVAILABLE, reason="python-lzo library not available")
class TestLZOStreaming:
    """Block-framed LZO files must be processed lazily in bounded memory."""

    ROWS = 200_000  # ~ tens of MB of plaintext

    def _write_large(self, path):
        codecobj = LZOCodec(path, mode="w")
        iterable = CSVIterable(codec=codecobj, mode="w", keys=["id", "name"])
        try:
            for i in range(self.ROWS):
                iterable.write({"id": str(i), "name": f"name-{i}-{'x' * 100}"})
        finally:
            iterable.close()

    def test_framed_read_is_lazy_wrapper(self, tmp_path):
        import io

        path = str(tmp_path / "large.csv.lzo")
        self._write_large(path)
        codecobj = LZOCodec(path, mode="r")
        fobj = codecobj.open()
        assert isinstance(fobj, io.BufferedReader), "framed LZO should stream, not buffer into BytesIO"
        codecobj.close()

    def test_large_roundtrip_bounded_memory(self, tmp_path):
        import tracemalloc

        path = str(tmp_path / "large.csv.lzo")
        self._write_large(path)
        uncompressed_size = self.ROWS * 110

        codecobj = LZOCodec(path, mode="r")
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
