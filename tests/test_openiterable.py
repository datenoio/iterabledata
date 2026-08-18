import pytest
from fixdata import FIXTURES, FIXTURES_TYPES

from iterable.helpers.detect import open_iterable


class TestOpenIterable:
    def test_iterate_plain_csv(self):
        iterable = open_iterable("fixtures/2cols6rows.csv")
        n = 0
        for row in iterable:
            assert set(dict(row).keys()) == set(dict(FIXTURES[n]).keys())
            n += 1
        iterable.close()

    #    def test_iterate_plain_delimiter_notmatch_csv(self):
    #        iterable = open_iterable('fixtures/2cols6rows.csv', iterableargs={'delimiter' : ';'})
    #        n = 0
    #        for row in iterable:
    #            assert row != FIXTURES[n]
    #            n += 1
    #        iterable.close()

    def test_iterate_gzip_csv(self):
        iterable = open_iterable("fixtures/2cols6rows.csv.gz")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_iterate_lzma_csv(self):
        iterable = open_iterable("fixtures/2cols6rows.csv.xz")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_iterate_zstd_csv(self):
        pytest.importorskip("zstandard", reason="zstandard is required for Zstandard support")
        iterable = open_iterable("fixtures/2cols6rows.csv.zst")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_iterate_brotli_csv(self):
        pytest.importorskip("brotli_file", reason="brotli_file is required for Brotli support")
        iterable = open_iterable("fixtures/2cols6rows.csv.br")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_iterate_bzip2_csv(self):
        iterable = open_iterable("fixtures/2cols6rows.csv.bz2")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_iterate_lz4_csv(self):
        pytest.importorskip("lz4", reason="lz4 is required for LZ4 support")
        iterable = open_iterable("fixtures/2cols6rows.csv.lz4")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_iterate_plain_xls(self):
        pytest.importorskip("xlrd", reason="xlrd is required for XLS support")
        iterable = open_iterable("fixtures/2cols6rows.xls")
        n = 0
        for row in iterable:
            assert row == FIXTURES_TYPES[n]
            n += 1
        iterable.close()

    def test_iterate_plain_xlsx(self):
        pytest.importorskip("openpyxl", reason="openpyxl is required for XLSX support")
        iterable = open_iterable("fixtures/2cols6rows.xlsx")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_iterate_plain_dbf(self):
        pytest.importorskip("dbfread", reason="dbfread is required for DBF support")
        iterable = open_iterable("fixtures/2cols6rows.dbf")
        n = 0
        for row in iterable:
            # DBF returns numeric id as int and field names are uppercase
            assert row["ID"] == int(FIXTURES[n]["id"])
            assert row["NAME"] == FIXTURES[n]["name"]
            n += 1
        iterable.close()

    def test_iterate_plain_parquet(self):
        pytest.importorskip("pyarrow", reason="pyarrow is required for Parquet support")
        iterable = open_iterable("fixtures/2cols6rows.parquet")
        n = 0
        for row in iterable:
            assert row == FIXTURES_TYPES[n]
            n += 1
        iterable.close()

    def test_iterate_plain_orc(self):
        pytest.importorskip("pyorc", reason="pyorc is required for ORC support")
        iterable = open_iterable("fixtures/2cols6rows.orc")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_iterate_plain_avro(self):
        pytest.importorskip("avro", reason="avro is required for Avro support")
        iterable = open_iterable("fixtures/2cols6rows.avro")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_iterate_plain_bson(self):
        pytest.importorskip("bson", reason="pymongo/bson is required for BSON support")
        iterable = open_iterable("fixtures/2cols6rows_flat.bson")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_iterate_plain_json(self):
        iterable = open_iterable("fixtures/2cols6rows_array.json")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_iterate_plain_jsonl(self):
        iterable = open_iterable("fixtures/2cols6rows_flat.jsonl")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_iterate_plain_xml(self):
        pytest.importorskip("lxml", reason="lxml is required for XML support")
        iterable = open_iterable("fixtures/books.xml", iterableargs={"tagname": "book"})
        n = 0
        years = [2005, 2005, 2003]
        for row in iterable:
            assert int(row["year"]) == years[n]
            n += 1
        iterable.close()

    def test_iterate_lz4_xml(self):
        pytest.importorskip("lz4", reason="lz4 is required for LZ4 support")
        pytest.importorskip("lxml", reason="lxml is required for XML support")
        iterable = open_iterable("fixtures/books.xml.lz4", iterableargs={"tagname": "book"})
        n = 0
        years = [2005, 2005, 2003]
        for row in iterable:
            assert int(row["year"]) == years[n]
            n += 1
        iterable.close()
