from fixdata import FIXTURES
from optional_datatypes import require_codec

from iterable.datatypes import CSVIterable

LZ4Codec = require_codec("LZ4Codec")


class TestLZ4:
    def test_fileexts(self):
        assert LZ4Codec.fileexts() == [
            "lz4",
        ]

    def test_openclose(self):
        codecobj = LZ4Codec("fixtures/2cols6rows.csv.lz4", mode="r")
        iterable = CSVIterable(codec=codecobj)
        iterable.close()

    def test_parsesimple_readone(self):
        codecobj = LZ4Codec("fixtures/2cols6rows.csv.lz4", mode="r")
        iterable = CSVIterable(codec=codecobj)
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.close()

    def test_parsesimple_reset(self):
        codecobj = LZ4Codec("fixtures/2cols6rows.csv.lz4", mode="r")
        iterable = CSVIterable(codec=codecobj)
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = iterable.read()
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_next(self):
        codecobj = LZ4Codec("fixtures/2cols6rows.csv.lz4", mode="r")
        iterable = CSVIterable(codec=codecobj)
        row = next(iterable)
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = next(iterable)
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_count(self):
        codecobj = LZ4Codec("fixtures/2cols6rows.csv.lz4", mode="r")
        iterable = CSVIterable(codec=codecobj)
        n = 0
        for _row in iterable:
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_parsesimple_iterateall(self):
        codecobj = LZ4Codec("fixtures/2cols6rows.csv.lz4", mode="r")
        iterable = CSVIterable(codec=codecobj)
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_write_read(self):
        codecobj = LZ4Codec("testdata/2cols6rows_test.csv.lz4", mode="w")
        iterable = CSVIterable(codec=codecobj, mode="w", keys=["id", "name"])
        for row in FIXTURES:
            iterable.write(row)
        iterable.close()
        codecobj = LZ4Codec("fixtures/2cols6rows.csv.lz4", mode="r")
        iterable = CSVIterable(codec=codecobj)
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        assert n == len(FIXTURES)
        iterable.close()
