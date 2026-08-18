import pytest
from fixdata import FIXTURES_BOOKS

pytest.importorskip("lxml", reason="lxml is required for XML support")

from iterable.datatypes import XMLIterable  # noqa: E402


class TestXML:
    def test_id(self):
        datatype_id = XMLIterable.id()
        assert datatype_id == "xml"

    def test_flatonly(self):
        flag = XMLIterable.is_flatonly()
        assert not flag

    def test_openclose(self):
        iterable = XMLIterable("fixtures/books.xml", tagname="book")
        iterable.close()

    def test_read_bulk_with_tag(self):
        iterable = XMLIterable("fixtures/books.xml", tagname="book")
        chunk = iterable.read_bulk(2)
        assert len(chunk) == 2
        years = [2005, 2005, 2003]
        assert int(chunk[0]["year"]) == years[0]
        assert int(chunk[1]["year"]) == years[1]
        iterable.close()

    def test_parsesimple_readone(self):
        iterable = XMLIterable("fixtures/books.xml", tagname="book")
        row = iterable.read()
        assert row == FIXTURES_BOOKS[0]
        iterable.close()

    def test_parsesimple_reset(self):
        iterable = XMLIterable("fixtures/books.xml", tagname="book")
        row = iterable.read()
        assert row == FIXTURES_BOOKS[0]
        iterable.reset()
        row_reset = iterable.read()
        assert row_reset == FIXTURES_BOOKS[0]
        iterable.close()

    def test_parsesimple_next(self):
        iterable = XMLIterable("fixtures/books.xml", tagname="book")
        row = next(iterable)
        assert row == FIXTURES_BOOKS[0]
        iterable.reset()
        row_reset = next(iterable)
        assert row_reset == FIXTURES_BOOKS[0]
        iterable.close()

    def test_parsesimple_count(self):
        iterable = XMLIterable("fixtures/books.xml", tagname="book")
        n = 0
        for _row in iterable:
            n += 1
        assert n == len(FIXTURES_BOOKS)
        iterable.close()

    def test_parsesimple_iterateall(self):
        iterable = XMLIterable("fixtures/books.xml", tagname="book")
        n = 0
        for row in iterable:
            assert row == FIXTURES_BOOKS[n]
            n += 1
        iterable.close()

    def test_has_tables(self):
        """Test has_tables static method"""
        assert XMLIterable.has_tables() is True

    def test_list_tables(self):
        """Test list_tables with XML file"""
        iterable = XMLIterable("fixtures/books.xml", tagname="book")
        tables = iterable.list_tables("fixtures/books.xml")
        assert isinstance(tables, list)
        assert "book" in tables
        iterable.close()

    def test_list_tables_instance_method(self):
        """Test list_tables on already-opened instance"""
        iterable = XMLIterable("fixtures/books.xml", tagname="book")
        tables = iterable.list_tables()
        assert isinstance(tables, list)
        assert "book" in tables
        iterable.close()
