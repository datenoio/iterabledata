from fixdata import FIXTURES_TYPES
from optional_datatypes import require_datatype

XLSIterable = require_datatype("XLSIterable")


class TestXLS:
    def test_id(self):
        datatype_id = XLSIterable.id()
        assert datatype_id == "xls"

    def test_flatonly(self):
        flag = XLSIterable.is_flatonly()
        assert flag

    def test_openclose(self):
        iterable = XLSIterable("fixtures/2cols6rows.xls")
        iterable.close()

    def test_parsesimple_readone(self):
        iterable = XLSIterable("fixtures/2cols6rows.xls")
        row = iterable.read()
        assert row == FIXTURES_TYPES[0]
        iterable.close()

    def test_parsesimple_fixedkeys_readone(self):
        iterable = XLSIterable("fixtures/2cols6rows.xls", keys=["id", "name"], start_line=1)
        row = iterable.read()
        assert row == FIXTURES_TYPES[0]
        iterable.close()

    def test_parsesimple_reset(self):
        iterable = XLSIterable("fixtures/2cols6rows.xls")
        row = iterable.read()
        assert row == FIXTURES_TYPES[0]
        iterable.reset()
        row_reset = iterable.read()
        assert row_reset == FIXTURES_TYPES[0]
        iterable.close()

    def test_parsesimple_next(self):
        iterable = XLSIterable("fixtures/2cols6rows.xls")
        row = next(iterable)
        assert row == FIXTURES_TYPES[0]
        iterable.reset()
        row_reset = next(iterable)
        assert row_reset == FIXTURES_TYPES[0]
        iterable.close()

    def test_parsesimple_count(self):
        iterable = XLSIterable("fixtures/2cols6rows.xls")
        n = 0
        for _row in iterable:
            n += 1
        assert n == len(FIXTURES_TYPES)
        iterable.close()

    def test_parsesimple_iterateall(self):
        iterable = XLSIterable("fixtures/2cols6rows.xls")
        n = 0
        for row in iterable:
            assert row == FIXTURES_TYPES[n]
            n += 1
        iterable.close()

    def test_parsesimple_fixedkeys_iterateall(self):
        iterable = XLSIterable("fixtures/2cols6rows.xls", keys=["id", "name"], start_line=1)
        n = 0
        for row in iterable:
            assert row == FIXTURES_TYPES[n]
            n += 1
        iterable.close()

    def test_has_tables(self):
        """Test has_tables static method"""
        assert XLSIterable.has_tables() is True

    def test_list_tables_instance_method(self):
        """Test list_tables on an already-opened instance"""
        iterable = XLSIterable("fixtures/2cols6rows.xls")
        sheets = iterable.list_tables()
        assert isinstance(sheets, list)
        assert len(sheets) > 0
        # Sheet name may be localized (e.g., "Sheet1", "Лист1"), just check it's a string
        assert isinstance(sheets[0], str)
        assert len(sheets[0]) > 0
        iterable.close()

    def test_list_tables_with_filename(self):
        """Test list_tables with filename parameter (class-like usage)"""
        iterable = XLSIterable("fixtures/2cols6rows.xls")
        sheets = iterable.list_tables("fixtures/2cols6rows.xls")
        assert isinstance(sheets, list)
        assert len(sheets) > 0
        iterable.close()

    def test_list_tables_reuses_workbook(self):
        """Test that list_tables reuses open workbook"""
        iterable = XLSIterable("fixtures/2cols6rows.xls")
        # Read a row to ensure workbook is open
        _ = iterable.read()
        # Now list tables - should reuse workbook
        sheets1 = iterable.list_tables()
        sheets2 = iterable.list_tables()
        assert sheets1 == sheets2
        iterable.close()
