import io

import pytest
from fixdata import FIXTURES

pytest.importorskip("dbfread", reason="dbfread is required for DBF support")

from iterable.datatypes import DBFIterable  # noqa: E402
from iterable.exceptions import ReadError  # noqa: E402


class TestDBF:
    def test_id(self):
        datatype_id = DBFIterable.id()
        assert datatype_id == "dbf"

    def test_flatonly(self):
        flag = DBFIterable.is_flatonly()
        assert flag

    def test_openclose(self):
        iterable = DBFIterable("fixtures/2cols6rows.dbf")
        iterable.close()

    def test_parsesimple_readone(self):
        iterable = DBFIterable("fixtures/2cols6rows.dbf")
        row = iterable.read()
        # DBF returns numeric id as int and field names are uppercase
        assert row["ID"] == int(FIXTURES[0]["id"])
        assert row["NAME"] == FIXTURES[0]["name"]
        iterable.close()

    def test_parsesimple_reset(self):
        iterable = DBFIterable("fixtures/2cols6rows.dbf")
        row = iterable.read()
        assert row["ID"] == int(FIXTURES[0]["id"])
        assert row["NAME"] == FIXTURES[0]["name"]
        iterable.reset()
        row_reset = iterable.read()
        assert row_reset["ID"] == int(FIXTURES[0]["id"])
        assert row_reset["NAME"] == FIXTURES[0]["name"]
        iterable.close()

    def test_parsesimple_next(self):
        iterable = DBFIterable("fixtures/2cols6rows.dbf")
        row = next(iterable)
        assert row["ID"] == int(FIXTURES[0]["id"])
        assert row["NAME"] == FIXTURES[0]["name"]
        iterable.reset()
        row_reset = next(iterable)
        assert row_reset["ID"] == int(FIXTURES[0]["id"])
        assert row_reset["NAME"] == FIXTURES[0]["name"]
        iterable.close()

    def test_parsesimple_count(self):
        iterable = DBFIterable("fixtures/2cols6rows.dbf")
        n = 0
        for _row in iterable:
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_parsesimple_iterateall(self):
        iterable = DBFIterable("fixtures/2cols6rows.dbf")
        n = 0
        for row in iterable:
            assert row["ID"] == int(FIXTURES[n]["id"])
            assert row["NAME"] == FIXTURES[n]["name"]
            n += 1
        iterable.close()

    def test_totals(self):
        iterable = DBFIterable("fixtures/2cols6rows.dbf")
        totals = iterable.totals()
        assert totals == len(FIXTURES)
        iterable.close()

    def test_has_totals(self):
        has_totals = DBFIterable.has_totals()
        assert has_totals

    def test_read_bulk_advances_and_stops(self):
        iterable = DBFIterable("fixtures/2cols6rows.dbf")
        chunk = iterable.read_bulk(4)
        assert len(chunk) == 4
        # Verify first 4 records
        for i in range(4):
            assert chunk[i]["ID"] == int(FIXTURES[i]["id"])
            assert chunk[i]["NAME"] == FIXTURES[i]["name"]
        # Next read should give the 5th row
        row = iterable.read()
        assert row["ID"] == int(FIXTURES[4]["id"])
        assert row["NAME"] == FIXTURES[4]["name"]
        # Exhaust
        _ = iterable.read()
        with pytest.raises(StopIteration):
            _ = iterable.read()
        iterable.close()

    def test_encoding_option(self):
        iterable = DBFIterable("fixtures/2cols6rows.dbf", options={"encoding": "utf-8"})
        row = iterable.read()
        assert row["ID"] == int(FIXTURES[0]["id"])
        assert row["NAME"] == FIXTURES[0]["name"]
        iterable.close()

    def test_requires_filename_not_stream(self):
        """DBF requires a file path; stream/codec raises ReadError."""
        with pytest.raises(ReadError) as exc_info:
            DBFIterable(stream=io.BytesIO(b"x"))
        assert "file path" in str(exc_info.value).lower() or "filename" in str(exc_info.value).lower()
