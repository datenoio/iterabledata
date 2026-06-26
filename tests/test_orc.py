from fixdata import FIXTURES

from iterable.datatypes import ORCIterable


class TestORC:
    def test_id(self):
        datatype_id = ORCIterable.id()
        assert datatype_id == "orc"

    def test_flatonly(self):
        flag = ORCIterable.is_flatonly()
        assert flag

    def test_openclose(self):
        iterable = ORCIterable("fixtures/2cols6rows.orc")
        iterable.close()

    def test_parsesimple_readone(self):
        iterable = ORCIterable("fixtures/2cols6rows.orc")
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.close()

    def test_parsesimple_reset(self):
        iterable = ORCIterable("fixtures/2cols6rows.orc")
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = iterable.read()
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_next(self):
        iterable = ORCIterable("fixtures/2cols6rows.orc")
        row = next(iterable)
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = next(iterable)
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_count(self):
        iterable = ORCIterable("fixtures/2cols6rows.orc")
        n = 0
        for _row in iterable:
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_parsesimple_iterateall(self):
        iterable = ORCIterable("fixtures/2cols6rows.orc")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_write_read(self):
        iterable = ORCIterable("fixtures/2cols6rows_test.orc", mode="w", keys=["id", "name"])
        iterable.write_bulk(FIXTURES)
        iterable.close()
        iterable = ORCIterable("fixtures/2cols6rows_test.orc", mode="r")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_write_read_infer_schema(self):
        # Writer should infer the schema from the data when no keys/schema given.
        iterable = ORCIterable("fixtures/2cols6rows_infer.orc", mode="w")
        iterable.write_bulk(FIXTURES)
        iterable.close()
        iterable = ORCIterable("fixtures/2cols6rows_infer.orc", mode="r")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_write_read_special_field_names(self):
        # Field names with spaces, commas, colons, empty, and non-ASCII chars
        # must not break the pyorc schema (built via pyorc.Struct, not a string).
        records = [
            {"full name": "Alice", "id:code": "1", "a,b": "x", "": "z", "naïve": "y"},
            {"full name": "Bob", "id:code": "2", "a,b": "p", "": "r", "naïve": "q"},
        ]
        iterable = ORCIterable("fixtures/special_names.orc", mode="w")
        iterable.write_bulk(records)
        iterable.close()
        iterable = ORCIterable("fixtures/special_names.orc", mode="r")
        out = list(iterable)
        iterable.close()
        assert out == records
