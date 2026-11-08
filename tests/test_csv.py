import codecs

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


GERMAN_ROWS = "Straße;PLZ;Ort\nMüllerstraße 1;10115;Berlin\nKönigsallee 2;40212;Düsseldorf\n"


@pytest.mark.parametrize(
    ("suffix", "compress"),
    [(".csv.gz", "gzip"), (".csv.bz2", "bz2"), (".csv.xz", "lzma")],
)
def test_encoding_of_compressed_csv_is_detected(tmp_path, suffix, compress):
    import importlib

    from iterable.helpers.detect import open_iterable

    module = importlib.import_module(compress)
    path = tmp_path / ("cp1252" + suffix)
    path.write_bytes(module.compress(GERMAN_ROWS.encode("cp1252")))
    with open_iterable(str(path), iterableargs={"autodetect": True}) as source:
        rows = list(source)
        assert codecs.lookup(source.encoding).name == "cp1252"
        assert source.delimiter == ";"
    assert rows[0] == {"Straße": "Müllerstraße 1", "PLZ": "10115", "Ort": "Berlin"}


def test_encoding_of_compressed_cp932_csv_is_detected(tmp_path):
    import gzip

    from iterable.helpers.detect import open_iterable

    text = "名称,住所,電話番号\n" + "大津市役所,滋賀県大津市御陵町3-1,077-523-1234\n" * 30
    path = tmp_path / "jp.csv.gz"
    path.write_bytes(gzip.compress(text.encode("cp932")))
    with open_iterable(str(path)) as source:
        rows = list(source)
        assert source.encoding.lower().replace("_", "") in ("cp932", "shiftjis")
    assert rows[0]["住所"] == "滋賀県大津市御陵町3-1"


def test_encoding_of_compressed_zstandard_csv_is_detected(tmp_path):
    zstd = pytest.importorskip("zstandard")
    from iterable.helpers.detect import open_iterable

    path = tmp_path / "cp1252.csv.zst"
    path.write_bytes(zstd.ZstdCompressor().compress(GERMAN_ROWS.encode("cp1252")))
    with open_iterable(str(path), iterableargs={"autodetect": True}) as source:
        assert next(source) == {"Straße": "Müllerstraße 1", "PLZ": "10115", "Ort": "Berlin"}


def test_explicit_encoding_of_compressed_csv_is_kept(tmp_path):
    import gzip

    from iterable.helpers.detect import open_iterable

    path = tmp_path / "rows.csv.gz"
    path.write_bytes(gzip.compress("id,name\n1,abc\n".encode("cp1251")))
    with open_iterable(str(path), iterableargs={"encoding": "cp1251"}) as source:
        assert source.encoding == "cp1251"
        assert list(source) == [{"id": "1", "name": "abc"}]


def test_short_cp1252_file_is_not_read_as_a_mac_code_page(tmp_path):
    from iterable.helpers.detect import open_iterable

    path = tmp_path / "plain.csv"
    path.write_bytes(GERMAN_ROWS.encode("cp1252"))
    with open_iterable(str(path), iterableargs={"autodetect": True}) as source:
        rows = list(source)
        assert source.encoding == "cp1252"
    assert list(rows[0]) == ["Straße", "PLZ", "Ort"]
    assert rows[1]["Ort"] == "Düsseldorf"


def test_mac_and_iso_results_are_mapped_to_windows_code_pages():
    from iterable.datatypes.csv import _windows_code_page

    sample = "Straße".encode("cp1252")
    assert _windows_code_page({"encoding": "MacTurkish"}, sample)["encoding"] == "cp1252"
    assert _windows_code_page({"encoding": "MacRoman"}, sample)["encoding"] == "cp1252"
    turkish = "İstanbul şehir".encode("cp1254")
    assert _windows_code_page({"encoding": "MacTurkish"}, turkish)["encoding"] == "cp1254"
    quotes = "“quoted” – text".encode("cp1252")
    assert _windows_code_page({"encoding": "ISO-8859-1"}, quotes)["encoding"] == "cp1252"
    assert _windows_code_page({"encoding": "ISO-8859-1"}, sample)["encoding"] == "ISO-8859-1"
    assert _windows_code_page({"encoding": "windows-1251"}, sample)["encoding"] == "windows-1251"


def test_sep_hint_line_sets_the_delimiter_and_is_skipped(tmp_path):
    from iterable.helpers.detect import open_iterable

    path = tmp_path / "excel.csv"
    path.write_text("sep=;\nName;PLZ;E-Mail\nSchule A;10115;info@a.de\nSchule B;40212;info@b.de\n")
    for args in ({}, {"autodetect": True}):
        with open_iterable(str(path), iterableargs=args) as source:
            rows = list(source)
            assert source.delimiter == ";"
            assert source.totals() == 2
        assert rows == [
            {"Name": "Schule A", "PLZ": "10115", "E-Mail": "info@a.de"},
            {"Name": "Schule B", "PLZ": "40212", "E-Mail": "info@b.de"},
        ]


def test_sep_hint_with_a_bom_tab_and_explicit_delimiter(tmp_path):
    from iterable.datatypes.csv import sep_hint
    from iterable.helpers.detect import open_iterable

    bom = chr(0xFEFF)
    assert sep_hint(bom + "sep=;\r\n") == ";"
    assert sep_hint("SEP=|\n") == "|"
    assert sep_hint("sep=;x\n") is None
    assert sep_hint("name;sep\n") is None
    path = tmp_path / "tab.csv"
    path.write_bytes((bom + "sep=\t\nName\tPLZ\nA\t1\n").encode("utf-8"))
    with open_iterable(str(path)) as source:
        assert source.delimiter == "\t"
        assert list(source) == [{"Name": "A", "PLZ": "1"}]
    path = tmp_path / "given.csv"
    path.write_text("sep=;\na,b\n1,2\n")
    with open_iterable(str(path), iterableargs={"delimiter": ","}) as source:
        assert list(source) == [{"a": "1", "b": "2"}]


TITLE_ROWS = (
    "Tabelle 12411-01: Bevölkerung nach Gemeinden\nStichtag: 31.12.2024\n\n"
    "AGS;Gemeinde;Einwohner\n11000000;Berlin;3685265\n02000000;Hamburg;1862565\n"
)


def test_skip_rows_drops_title_lines_before_the_header(tmp_path):
    from iterable.helpers.detect import open_iterable

    path = tmp_path / "genesis.csv"
    path.write_text(TITLE_ROWS)
    for args in ({"skip_rows": 3, "autodetect": True}, {"skip_rows": 3, "delimiter": ";"}):
        with open_iterable(str(path), iterableargs=args) as source:
            rows = list(source)
            assert source.delimiter == ";"
            assert source.totals() == 2
            source.reset()
            assert next(source)["Gemeinde"] == "Berlin"
        assert rows[1] == {"AGS": "02000000", "Gemeinde": "Hamburg", "Einwohner": "1862565"}


def test_skip_rows_and_sep_hint_through_codecs(tmp_path):
    import gzip

    from iterable.helpers.detect import open_iterable

    path = tmp_path / "genesis.csv.gz"
    path.write_bytes(gzip.compress(("sep=;\n" + TITLE_ROWS).encode("cp1252")))
    with open_iterable(str(path), iterableargs={"skip_rows": 3}) as source:
        rows = list(source)
        assert codecs.lookup(source.encoding).name == "cp1252"
    assert rows[0] == {"AGS": "11000000", "Gemeinde": "Berlin", "Einwohner": "3685265"}


def test_skip_rows_must_be_a_non_negative_integer(tmp_path):
    from iterable.datatypes.csv import CSVIterable

    path = tmp_path / "rows.csv"
    path.write_text("a\n1\n")
    for bad in (-1, "2", 1.5, True):
        with pytest.raises(ValueError, match="skip_rows"):
            CSVIterable(str(path), options={"skip_rows": bad})
