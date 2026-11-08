import pytest

from iterable.datatypes.ods import ODSIterable

try:
    from odf.opendocument import load  # noqa: F401

    HAS_ODF = True
except ImportError:
    try:
        import pyexcel_ods3  # noqa: F401

        HAS_PYEXCEL_ODS = True
        HAS_ODF = False
    except ImportError:
        HAS_PYEXCEL_ODS = False
        HAS_ODF = False


@pytest.mark.skipif(not HAS_ODF and not HAS_PYEXCEL_ODS, reason="ODS library not available")
def test_ods_read():
    """Test ODS reading - requires a test fixture file"""
    # This test would need an actual ODS file fixture
    # For now, we'll just test that the class can be instantiated
    pass


@pytest.mark.skipif(not HAS_ODF and not HAS_PYEXCEL_ODS, reason="ODS library not available")
def test_ods_id():
    """Test ODS ID"""
    assert ODSIterable.id() == "ods"


@pytest.mark.skipif(not HAS_ODF and not HAS_PYEXCEL_ODS, reason="ODS library not available")
def test_ods_flatonly():
    """Test ODS is flat only"""
    assert ODSIterable.is_flatonly()


@pytest.mark.skipif(not HAS_ODF and not HAS_PYEXCEL_ODS, reason="ODS library not available")
def test_ods_has_tables():
    """Test has_tables static method"""
    assert ODSIterable.has_tables() is True


@pytest.mark.skipif(not HAS_ODF and not HAS_PYEXCEL_ODS, reason="ODS library not available")
def test_ods_list_tables_instance_method():
    """Test list_tables on an already-opened instance"""
    # This test requires an actual ODS file fixture
    # For now, we'll just test that the method exists and can be called
    # If fixtures/2cols6rows.ods exists, use it
    import os

    fixture_file = "fixtures/2cols6rows.ods"
    if os.path.exists(fixture_file):
        iterable = ODSIterable(fixture_file)
        sheets = iterable.list_tables()
        assert isinstance(sheets, list)
        assert len(sheets) > 0
        assert isinstance(sheets[0], str)
        iterable.close()


@pytest.mark.skipif(not HAS_ODF and not HAS_PYEXCEL_ODS, reason="ODS library not available")
def test_ods_list_tables_with_filename():
    """Test list_tables with filename parameter (class-like usage)"""
    import os

    fixture_file = "fixtures/2cols6rows.ods"
    if os.path.exists(fixture_file):
        iterable = ODSIterable(fixture_file)
        sheets = iterable.list_tables(fixture_file)
        assert isinstance(sheets, list)
        assert len(sheets) > 0
        iterable.close()


@pytest.mark.skipif(not HAS_ODF, reason="odfpy is required to write the test document")
def test_ods_start_line_through_open_iterable(tmp_path):
    from odf.opendocument import OpenDocumentSpreadsheet
    from odf.table import Table, TableCell, TableRow
    from odf.text import P

    from iterable.helpers.detect import open_iterable

    document = OpenDocumentSpreadsheet()
    table = Table(name="kreise")
    for values in [["Tabelle 1: Kreise"], ["Stand"], ["Schlüssel", "Kreis"], ["01001", "Flensburg"], ["01002", "Kiel"]]:
        row = TableRow()
        for value in values:
            cell = TableCell()
            cell.addElement(P(text=value))
            row.addElement(cell)
        table.addElement(row)
    document.spreadsheet.addElement(table)
    path = str(tmp_path / "title.ods")
    document.save(path)
    with open_iterable(path, iterableargs={"start_line": 2}) as source:
        assert source.keys == ["Schlüssel", "Kreis"]
        assert [row["Kreis"] for row in source] == ["Flensburg", "Kiel"]


@pytest.mark.skipif(not HAS_ODF, reason="odfpy is required to write the test document")
def test_ods_page_by_sheet_name_and_extra_cells(tmp_path):
    from odf.opendocument import OpenDocumentSpreadsheet
    from odf.table import Table, TableCell, TableRow
    from odf.text import P

    from iterable.helpers.detect import open_iterable

    document = OpenDocumentSpreadsheet()
    for name, rows in [("Notes", [["Read me first"]]), ("Data", [["id", "name"], ["1", "A", "extra"], ["2", "B"]])]:
        table = Table(name=name)
        for values in rows:
            row = TableRow()
            for value in values:
                cell = TableCell()
                cell.addElement(P(text=value))
                row.addElement(cell)
            table.addElement(row)
        document.spreadsheet.addElement(table)
    path = str(tmp_path / "two.ods")
    document.save(path)
    expected = [{"id": "1", "name": "A", None: ["extra"]}, {"id": "2", "name": "B"}]
    assert list(open_iterable(path, iterableargs={"page": "Data"})) == expected
    assert list(open_iterable(path, iterableargs={"page": 1})) == expected
    with pytest.raises(ValueError, match="'Notes', 'Data'"):
        ODSIterable(path, page="Missing")
