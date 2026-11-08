import pytest
from fixdata import FIXTURES

from iterable.datatypes import CSVIterable


def test_csv_has_tables():
    """Test CSV doesn't support tables"""
    assert CSVIterable.has_tables() is False


def test_csv_list_tables():
    """Test CSV list_tables returns None"""
    iterable = CSVIterable("fixtures/2cols6rows.csv")
    assert iterable.list_tables() is None
    assert iterable.list_tables("fixtures/2cols6rows.csv") is None
    iterable.close()


class TestCSV:
    def test_id(self):
        datatype_id = CSVIterable.id()
        assert datatype_id == "csv"

    def test_flatonly(self):
        flag = CSVIterable.is_flatonly()
        assert flag

    def test_openclose(self):
        iterable = CSVIterable("fixtures/2cols6rows.csv")
        iterable.close()

    def test_parsesimple_readone(self):
        iterable = CSVIterable("fixtures/2cols6rows.csv")
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.close()

    def test_parsesimple_reset(self):
        iterable = CSVIterable("fixtures/2cols6rows.csv")
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = iterable.read()
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_next(self):
        iterable = CSVIterable("fixtures/2cols6rows.csv")
        row = next(iterable)
        assert row == FIXTURES[0]
        iterable.reset()
        row_reset = next(iterable)
        assert row_reset == FIXTURES[0]
        iterable.close()

    def test_parsesimple_count(self):
        iterable = CSVIterable("fixtures/2cols6rows.csv")
        n = 0
        for _row in iterable:
            n += 1
        assert n == len(FIXTURES)
        iterable.close()

    def test_parsesimple_iterateall(self):
        iterable = CSVIterable("fixtures/2cols6rows.csv")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_write_read(self):
        iterable = CSVIterable("testdata/2cols6rows_test.csv", mode="w", keys=["id", "name"])
        for row in FIXTURES:
            iterable.write(row)
        iterable.close()
        iterable = CSVIterable("testdata/2cols6rows_test.csv")
        n = 0
        for row in iterable:
            assert row == FIXTURES[n]
            n += 1
        iterable.close()

    def test_read_bulk_advances_and_stops(self):
        iterable = CSVIterable("fixtures/2cols6rows.csv")
        chunk = iterable.read_bulk(4)
        assert len(chunk) == 4
        assert chunk == FIXTURES[:4]
        # Next read should give the 5th row
        row = iterable.read()
        assert row == FIXTURES[4]
        # Exhaust
        _ = iterable.read()
        with pytest.raises(StopIteration):
            _ = iterable.read()
        iterable.close()


def test_detect_encoding_reads_a_bom_file_as_utf8_sig(tmp_path):
    from iterable.datatypes.csv import detect_encoding_raw

    path = tmp_path / "bom.csv"
    path.write_bytes("\ufeffid,name\n1,Иван\n".encode("utf-8"))
    assert detect_encoding_raw(filename=str(path))["encoding"] == "utf-8-sig"
    plain = tmp_path / "plain.csv"
    plain.write_bytes("id,name\n1,Иван\n".encode())
    assert detect_encoding_raw(filename=str(plain))["encoding"] == "utf-8"


def test_bom_does_not_stay_in_the_first_header(tmp_path):
    from iterable.helpers.detect import open_iterable

    path = tmp_path / "bom.csv"
    path.write_bytes("\ufeffasn,name\n2118,RELCOM-AS\n".encode("utf-8"))
    rows = list(open_iterable(str(path)))
    assert list(rows[0]) == ["asn", "name"]


def test_detect_encoding_tolerates_a_sample_cut_inside_a_character(tmp_path):
    from iterable.datatypes.csv import detect_encoding_raw

    path = tmp_path / "cut.csv"
    text = "name\n" + "Россия\n" * 20
    path.write_bytes(text.encode("utf-8"))
    limit = len("name\nР".encode()) - 1  # ends after the first byte of "Р"
    assert detect_encoding_raw(filename=str(path), limit=limit)["encoding"] == "utf-8"


def test_delimiter_autodetection_on_zstandard_file(tmp_path):
    zstd = pytest.importorskip("zstandard")
    from iterable.helpers.detect import open_iterable

    path = tmp_path / "rows.csv.zst"
    path.write_bytes(zstd.ZstdCompressor().compress(b"id;name\n1;a\n2;b\n"))
    source = open_iterable(str(path), iterableargs={"autodetect": True})
    rows = list(source)
    assert source.delimiter == ";"
    assert rows == [{"id": "1", "name": "a"}, {"id": "2", "name": "b"}]


def test_delimiter_autodetection_keeps_the_header_of_a_non_seekable_stream():
    import io

    from iterable.datatypes.csv import CSVIterable

    class OneWay(io.StringIO):
        def seekable(self):
            return False

    source = CSVIterable(stream=OneWay("id;name\n1;a\n"), autodetect=True)
    rows = list(source)
    # Detection would consume the header line; the stream keeps a comma instead.
    assert source.delimiter == ","
    assert list(rows[0]) == ["id;name"]
