import pytest
from fixdata import FIXTURES, FIXTURES_TYPES

pytest.importorskip("pyarrow", reason="pyarrow is required for Parquet support")

from iterable.datatypes import ParquetIterable  # noqa: E402


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

    def test_write_bulk_preserves_schema_with_varying_column_order(self, tmp_path):
        """Subsequent batches must match the first batch schema, including field order."""
        outfile = tmp_path / "varying_order.parquet"
        iterable = ParquetIterable(str(outfile), mode="w")
        first_batch = [
            {
                "_id": {"$oid": "1"},
                "count": 1,
                "gender": "m",
                "ethnic": ["slav"],
                "f_form": "A",
                "fname": "B",
                "text": "C",
            },
        ]
        second_batch = [
            {
                "_id": {"$oid": "2"},
                "count": 2,
                "f_form": "D",
                "gender": "f",
                "text": "E",
                "ethnic": ["slav"],
                "fname": "F",
            },
        ]
        iterable.write_bulk(first_batch)
        iterable.write_bulk(second_batch)
        iterable.close()

        reader = ParquetIterable(str(outfile), mode="r")
        rows = list(reader)
        reader.close()
        assert len(rows) == 2
        assert rows[0]["count"] == 1
        assert rows[1]["text"] == "E"

    def test_write_bulk_normalizes_mongodb_extended_json(self, tmp_path):
        """MongoDB extended JSON scalars must not mix with native types in one column."""
        outfile = tmp_path / "extended_json.parquet"
        iterable = ParquetIterable(str(outfile), mode="w")
        batch = [
            {"text": "Иван", "count": 100, "gender": "m"},
            {"text": "Эльмира", "count": {"$numberLong": "654"}, "gender": "f"},
        ]
        iterable.write_bulk(batch)
        iterable.close()

        reader = ParquetIterable(str(outfile), mode="r")
        rows = list(reader)
        reader.close()
        assert rows[0]["count"] == 100
        assert rows[1]["count"] == 654
