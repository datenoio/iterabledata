from fixdata import FIXTURES
from optional_datatypes import require_codec

from iterable.datatypes import CSVIterable

ZSTDCodec = require_codec("ZSTDCodec")


class TestZSTD:
    def test_fileexts(self):
        assert ZSTDCodec.fileexts() == ["zstd", "zst"]

    def test_openclose(self):
        codecobj = ZSTDCodec("fixtures/2cols6rows.csv.zst", mode="rb")
        iterable = CSVIterable(codec=codecobj)
        iterable.close()

    def test_parsesimple_readone(self):
        codecobj = ZSTDCodec("fixtures/2cols6rows.csv.zst", mode="rb")
        iterable = CSVIterable(codec=codecobj)
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.close()

    def test_parsesimple_reset(self):
        codecobj = ZSTDCodec("fixtures/2cols6rows.csv.zst", mode="rb")
        iterable = CSVIterable(codec=codecobj)
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = iterable.read()
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_next(self):
        codecobj = ZSTDCodec("fixtures/2cols6rows.csv.zst", mode="rb")
        iterable = CSVIterable(codec=codecobj)
        row = next(iterable)
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = next(iterable)
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_count(self):
        codecobj = ZSTDCodec("fixtures/2cols6rows.csv.zst", mode="rb")
        iterable = CSVIterable(codec=codecobj)
        n = 0
        for _row in iterable:
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_parsesimple_iterateall(self):
        codecobj = ZSTDCodec("fixtures/2cols6rows.csv.zst", mode="rb")
        iterable = CSVIterable(codec=codecobj)
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_write_read(self):
        codecobj = ZSTDCodec("testdata/2cols6rows_test.csv.zst", mode="wb")
        iterable = CSVIterable(codec=codecobj, mode="w", keys=["id", "name"])
        for row in FIXTURES:
            iterable.write(row)
        iterable.close()
        codecobj = ZSTDCodec("fixtures/2cols6rows.csv.zst", mode="rb")
        iterable = CSVIterable(codec=codecobj)
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        assert n == len(FIXTURES)
        iterable.close()
