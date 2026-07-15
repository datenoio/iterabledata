import warnings

import pytest
from fixdata import FIXTURES

from iterable.datatypes import PickleIterable

TESTING_DIR = "testdata"


class TestPickle:
    def test_id(self):
        datatype_id = PickleIterable.id()
        assert datatype_id == "pickle"

    def test_flatonly(self):
        flag = PickleIterable.is_flatonly()
        assert not flag

    def test_openclose(self):
        iterable = PickleIterable("fixtures/2cols6rows_flat.pickle")
        iterable.close()

    def test_parsesimple_readone(self):
        iterable = PickleIterable("fixtures/2cols6rows_flat.pickle")
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.close()

    def test_parsesimple_reset(self):
        iterable = PickleIterable("fixtures/2cols6rows_flat.pickle")
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = iterable.read()
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_next(self):
        iterable = PickleIterable("fixtures/2cols6rows_flat.pickle")
        row = next(iterable)
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = next(iterable)
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_count(self):
        iterable = PickleIterable("fixtures/2cols6rows_flat.pickle")
        n = 0
        for _row in iterable:
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_parsesimple_iterateall(self):
        iterable = PickleIterable("fixtures/2cols6rows_flat.pickle")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_read_warns_without_trust(self):
        with pytest.warns(UserWarning, match="trust=True"):
            iterable = PickleIterable("fixtures/2cols6rows_flat.pickle")
        iterable.close()

    def test_trust_option_suppresses_warning(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            iterable = PickleIterable("fixtures/2cols6rows_flat.pickle", options={"trust": True})
        assert iterable.read() == FIXTURES[0]
        iterable.close()

    def test_write_mode_does_not_warn(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            iterable = PickleIterable("testdata/trust_check.pickle", mode="w")
        iterable.close()

    def test_write_read(self):
        iterable = PickleIterable("testdata/2cols6rows_test.pickle", mode="w")
        for row in FIXTURES:
            iterable.write(row)
        iterable.close()
        iterable = PickleIterable("testdata/2cols6rows_test.pickle")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()
