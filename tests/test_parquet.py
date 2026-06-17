from fixdata import FIXTURES, FIXTURES_TYPES

from iterable.datatypes import ParquetIterable


def test_parquet_has_tables():
    """Test Parquet doesn't support tables"""
    assert ParquetIterable.has_tables() is False


def test_parquet_list_tables():
    """Test Parquet list_tables returns None"""
    iterable = ParquetIterable("fixtures/2cols6rows.parquet")
    assert iterable.list_tables() is None
    assert iterable.list_tables("fixtures/2cols6rows.parquet") is None
    iterable.close()


class TestParquet:
    def test_id(self):
        datatype_id = ParquetIterable.id()
        assert datatype_id == "parquet"

    def test_flatonly(self):
        flag = ParquetIterable.is_flatonly()
        assert flag

    def test_openclose(self):
        iterable = ParquetIterable("fixtures/2cols6rows.parquet")
        iterable.close()

    def test_read_bulk_returns_n_records(self):
        iterable = ParquetIterable("fixtures/2cols6rows.parquet")
        chunk = iterable.read_bulk(2)
        assert len(chunk) == 2
        from fixdata import FIXTURES_TYPES

        assert chunk == FIXTURES_TYPES[:2]
        iterable.close()

    def test_parsesimple_readone(self):
        iterable = ParquetIterable("fixtures/2cols6rows.parquet")
        row = iterable.read()
        assert row == FIXTURES_TYPES[0]
        iterable.close()

    def test_parsesimple_reset(self):
        iterable = ParquetIterable("fixtures/2cols6rows.parquet")
        row = iterable.read()
        assert row == FIXTURES_TYPES[0]
        iterable.reset()
        row_reset = iterable.read()
        assert row_reset == FIXTURES_TYPES[0]
        iterable.close()

    def test_parsesimple_next(self):
        iterable = ParquetIterable("fixtures/2cols6rows.parquet")
        row = next(iterable)
        assert row == FIXTURES_TYPES[0]
        iterable.reset()
        row_reset = next(iterable)
        assert row_reset == FIXTURES_TYPES[0]
        iterable.close()

    def test_parsesimple_count(self):
        iterable = ParquetIterable("fixtures/2cols6rows.parquet")
        n = 0
        for _row in iterable:
            n += 1
        assert n == len(FIXTURES_TYPES)
        iterable.close()

    def test_parsesimple_iterateall(self):
        iterable = ParquetIterable("fixtures/2cols6rows.parquet")
        n = 0
        for row in iterable:
            assert row == FIXTURES_TYPES[n]
            n += 1
        iterable.close()

    def test_write_read(self):
        iterable = ParquetIterable(
            "fixtures/2cols6rows_test.parquet", mode="w", keys=["id", "name"], use_pandas=True, compression="zstd"
        )
        iterable.write_bulk(FIXTURES)
        iterable.close()
        iterable = ParquetIterable("fixtures/2cols6rows_test.parquet", mode="r")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        assert n == len(FIXTURES)
        iterable.close()
