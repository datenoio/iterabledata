import os

import pytest

from iterable.datatypes import PXIterable

FIXTURE_FILE = "fixtures/2cols6rows.px"


@pytest.mark.skipif(not os.path.exists(FIXTURE_FILE), reason="PC-Axis fixture file not found")
class TestPX:
    def test_id(self):
        datatype_id = PXIterable.id()
        assert datatype_id == "px"

    def test_flatonly(self):
        flag = PXIterable.is_flatonly()
        assert flag

    def test_openclose(self):
        iterable = PXIterable(FIXTURE_FILE)
        iterable.close()

    def test_has_totals(self):
        iterable = PXIterable(FIXTURE_FILE)
        assert PXIterable.has_totals()
        total = iterable.totals()
        assert total == 18  # 3 ages * 2 genders * 3 years
        iterable.close()

    def test_read(self):
        iterable = PXIterable(FIXTURE_FILE)
        row = iterable.read()
        assert isinstance(row, dict)
        # Check that row has expected keys
        assert "Age" in row
        assert "Gender" in row
        assert "Year" in row
        assert "VALUE" in row
        iterable.close()

    def test_read_all(self):
        iterable = PXIterable(FIXTURE_FILE)
        rows = []
        try:
            while True:
                rows.append(iterable.read())
        except StopIteration:
            pass
        assert len(rows) == 18
        # Check first row
        assert rows[0]["Age"] == "0-4"
        assert rows[0]["Gender"] == "Male"
        assert rows[0]["Year"] == "2020"
        assert rows[0]["VALUE"] == 100
        iterable.close()

    def test_read_bulk(self):
        iterable = PXIterable(FIXTURE_FILE)
        chunk = iterable.read_bulk(5)
        assert len(chunk) == 5
        assert all(isinstance(row, dict) for row in chunk)
        iterable.close()

    def test_metadata(self):
        iterable = PXIterable(FIXTURE_FILE)
        # Check that metadata is parsed
        assert hasattr(iterable, "metadata")
        assert "TITLE" in iterable.metadata or "_TITLE" in iterable.read()
        iterable.close()

    def test_reset(self):
        iterable = PXIterable(FIXTURE_FILE)
        row1 = iterable.read()
        iterable.reset()
        row2 = iterable.read()
        # After reset, should read from beginning
        assert row1 == row2
        iterable.close()


PX_ANSI = (
    'CHARSET="ANSI";\nAXIS-VERSION="2000";\nLANGUAGE="de";\nMATRIX="test";\n'
    'TITLE="Bevölkerung nach Gemeinde";\nCONTENTS="Bevölkerung";\nUNITS="Personen";\n'
    'STUB="Gemeinde";\nHEADING="Jahr";\nVALUES("Gemeinde")="Zürich","Genève";\n'
    'VALUES("Jahr")="2000","2010";\nDATA=\n1 2\n3 4;\n'
)


def test_px_charset_ansi_is_read_as_cp1252(tmp_path):
    from iterable.helpers.detect import open_iterable

    path = tmp_path / "ansi.px"
    path.write_bytes(PX_ANSI.encode("cp1252"))
    with open_iterable(str(path)) as source:
        rows = list(source)
        assert source.encoding == "cp1252"
    assert [row["Gemeinde"] for row in rows] == ["Zürich", "Zürich", "Genève", "Genève"]
    assert rows[0]["_TITLE"] == "Bevölkerung nach Gemeinde"


def test_px_codepage_wins_over_charset(tmp_path):
    from iterable.helpers.detect import open_iterable

    text = PX_ANSI.replace('AXIS-VERSION="2000";', 'AXIS-VERSION="2000";\nCODEPAGE="iso-8859-15";')
    path = tmp_path / "latin9.px"
    path.write_bytes(text.replace("Personen", "€ Personen").encode("iso-8859-15"))
    with open_iterable(str(path)) as source:
        row = next(source)
        assert source.encoding == "iso-8859-15"
    assert row["_UNITS"] == "€ Personen"


def test_px_utf8_bom_and_explicit_encoding(tmp_path):
    from iterable.helpers.detect import open_iterable

    path = tmp_path / "bom.px"
    path.write_bytes(b"\xef\xbb\xbf" + PX_ANSI.encode("utf-8"))
    with open_iterable(str(path)) as source:
        assert next(source)["Gemeinde"] == "Zürich"
    latin = tmp_path / "latin.px"
    latin.write_bytes(PX_ANSI.encode("latin-1"))
    with open_iterable(str(latin), iterableargs={"encoding": "latin-1"}) as source:
        assert source.encoding == "latin-1"
        assert next(source)["Gemeinde"] == "Zürich"


def test_px_without_charset_is_dos(tmp_path):
    from iterable.datatypes.px import detect_px_encoding

    text = PX_ANSI.replace('CHARSET="ANSI";\n', "")
    assert detect_px_encoding(text.encode("cp850")) == "cp850"
    assert detect_px_encoding(text.encode("utf-8")) == "utf-8"


def test_px_metadata_option_leaves_out_keyword_copies(tmp_path):
    from iterable.helpers.detect import open_iterable

    path = tmp_path / "ansi.px"
    path.write_bytes(PX_ANSI.encode("cp1252"))
    with open_iterable(str(path), iterableargs={"metadata": False}) as source:
        assert next(source) == {"Gemeinde": "Zürich", "Jahr": "2000", "VALUE": 1}
    with open_iterable(str(path)) as source:
        assert "_CHARSET" in next(source)


def test_px_values_on_the_data_line(tmp_path):
    """INE writes the first values on the DATA= line itself (#50)."""
    from iterable.helpers.detect import open_iterable

    path = tmp_path / "ine.px"
    path.write_bytes(PX_ANSI.replace("DATA=\n1 2\n3 4;", "DATA=1 2\n3 4;").encode("cp1252"))
    with open_iterable(str(path), iterableargs={"metadata": False}) as source:
        assert [row["VALUE"] for row in source] == [1, 2, 3, 4]
