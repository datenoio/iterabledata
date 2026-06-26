import pytest
from fixdata import FIXTURES

from iterable.datatypes import AVROIterable


class TestAVRO:
    def test_id(self):
        datatype_id = AVROIterable.id()
        assert datatype_id == "avro"

    def test_flatonly(self):
        flag = AVROIterable.is_flatonly()
        assert flag

    def test_openclose(self):
        iterable = AVROIterable("fixtures/2cols6rows.avro")
        iterable.close()

    def test_parsesimple_readone(self):
        iterable = AVROIterable("fixtures/2cols6rows.avro")
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.close()

    def test_parsesimple_reset(self):
        iterable = AVROIterable("fixtures/2cols6rows.avro")
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = iterable.read()
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_next(self):
        iterable = AVROIterable("fixtures/2cols6rows.avro")
        row = next(iterable)
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = next(iterable)
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_count(self):
        iterable = AVROIterable("fixtures/2cols6rows.avro")
        n = 0
        for _row in iterable:
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_parsesimple_iterateall(self):
        iterable = AVROIterable("fixtures/2cols6rows.avro")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_write_read_with_keys(self):
        iterable = AVROIterable("fixtures/2cols6rows_test.avro", mode="w", keys=["id", "name"])
        iterable.write_bulk(FIXTURES)
        iterable.close()
        iterable = AVROIterable("fixtures/2cols6rows_test.avro", mode="r")
        out = list(iterable)
        iterable.close()
        assert out == FIXTURES

    def test_write_read_infer_schema(self):
        # Writer should infer the schema from the data when no keys/schema given.
        iterable = AVROIterable("fixtures/2cols6rows_infer.avro", mode="w")
        iterable.write_bulk(FIXTURES)
        iterable.close()
        iterable = AVROIterable("fixtures/2cols6rows_infer.avro", mode="r")
        out = list(iterable)
        iterable.close()
        assert out == FIXTURES

    def test_write_coerces_values_and_fills_missing(self):
        records = [{"id": 1, "name": "John"}, {"id": 2}]
        iterable = AVROIterable("fixtures/coerce.avro", mode="w", keys=["id", "name"])
        iterable.write_bulk(records)
        iterable.close()
        iterable = AVROIterable("fixtures/coerce.avro", mode="r")
        out = list(iterable)
        iterable.close()
        assert out == [{"id": "1", "name": "John"}, {"id": "2", "name": None}]

    def test_write_invalid_field_name_raises_with_keys(self):
        with pytest.raises(ValueError, match="field names must match"):
            AVROIterable("fixtures/invalid.avro", mode="w", keys=["full name"])

    def test_write_invalid_field_name_raises_inferred(self):
        # When schema is inferred lazily, the error surfaces on first write.
        iterable = AVROIterable("fixtures/invalid.avro", mode="w")
        with pytest.raises(ValueError, match="field names must match"):
            iterable.write_bulk([{"full name": "x"}])
        iterable.close()

    def test_writable_capability(self):
        from iterable.helpers.capabilities import supports_write

        assert supports_write("avro") is True
