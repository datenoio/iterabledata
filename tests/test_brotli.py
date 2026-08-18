from fixdata import FIXTURES
from optional_datatypes import require_codec

from iterable.datatypes import CSVIterable

BrotliCodec = require_codec("BrotliCodec")


class TestBrotli:
    def test_fileexts(self):
        assert BrotliCodec.fileexts() == ["br", "brotli"]

    def test_openclose(self):
        codecobj = BrotliCodec("fixtures/2cols6rows.csv.br", mode="r")
        iterable = CSVIterable(codec=codecobj)
        iterable.close()

    def test_parsesimple_readone(self):
        codecobj = BrotliCodec("fixtures/2cols6rows.csv.br", mode="r")
        iterable = CSVIterable(codec=codecobj)
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.close()

    def test_parsesimple_reset(self):
        codecobj = BrotliCodec("fixtures/2cols6rows.csv.br", mode="r")
        iterable = CSVIterable(codec=codecobj)
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = iterable.read()
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_next(self):
        codecobj = BrotliCodec("fixtures/2cols6rows.csv.br", mode="r")
        iterable = CSVIterable(codec=codecobj)
        row = next(iterable)
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = next(iterable)
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_count(self):
        codecobj = BrotliCodec("fixtures/2cols6rows.csv.br", mode="r")
        iterable = CSVIterable(codec=codecobj)
        n = 0
        for _row in iterable:
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_parsesimple_iterateall(self):
        codecobj = BrotliCodec("fixtures/2cols6rows.csv.br", mode="r")
        iterable = CSVIterable(codec=codecobj)
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_write_read(self):
        codecobj = BrotliCodec("testdata/2cols6rows_test.csv.br", mode="w")
        iterable = CSVIterable(codec=codecobj, mode="w", keys=["id", "name"])
        for row in FIXTURES:
            iterable.write(row)
        iterable.close()
        codecobj = BrotliCodec("fixtures/2cols6rows.csv.br", mode="r")
        iterable = CSVIterable(codec=codecobj)
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        assert n == len(FIXTURES)
        iterable.close()
