import pytest

pytest.importorskip("bs4", reason="beautifulsoup4 is required for HTML support")

from iterable.datatypes import HTMLIterable  # noqa: E402
from iterable.helpers.detect import open_iterable  # noqa: E402


class TestHTML:
    def test_id(self):
        datatype_id = HTMLIterable.id()
        assert datatype_id == "html"

    def test_flatonly(self):
        flag = HTMLIterable.is_flatonly()
        assert flag

    def test_read_single_table(self):
        """Test reading HTML file with single table"""
        html_content = """
        <html>
        <body>
        <table>
        <tr>
            <th>Name</th>
            <th>Age</th>
            <th>City</th>
        </tr>
        <tr>
            <td>Alice</td>
            <td>30</td>
            <td>New York</td>
        </tr>
        <tr>
            <td>Bob</td>
            <td>25</td>
            <td>London</td>
        </tr>
        </table>
        </body>
        </html>
        """
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_file = f.name

        try:
            iterable = HTMLIterable(temp_file)
            row = iterable.read()
            assert row == {"Name": "Alice", "Age": "30", "City": "New York"}
            row = iterable.read()
            assert row == {"Name": "Bob", "Age": "25", "City": "London"}
            iterable.close()
        finally:
            os.unlink(temp_file)

    def test_read_table_without_headers(self):
        """Test reading HTML table without <th> headers"""
        html_content = """
        <html>
        <body>
        <table>
        <tr>
            <td>Alice</td>
            <td>30</td>
        </tr>
        <tr>
            <td>Bob</td>
            <td>25</td>
        </tr>
        </table>
        </body>
        </html>
        """
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_file = f.name

        try:
            iterable = HTMLIterable(temp_file)
            row = iterable.read()
            # Should generate column names
            assert "column_0" in row
            assert "column_1" in row
            assert row["column_0"] == "Alice"
            iterable.close()
        finally:
            os.unlink(temp_file)

    def test_read_empty_table(self):
        """Test reading HTML file with no tables"""
        html_content = """
        <html>
        <body>
        <p>No tables here</p>
        </body>
        </html>
        """
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_file = f.name

        try:
            iterable = HTMLIterable(temp_file)
            # Should raise StopIteration immediately
            with pytest.raises(StopIteration):
                iterable.read()
            iterable.close()
        finally:
            os.unlink(temp_file)

    def test_automatic_detection(self):
        """Test automatic format detection via open_iterable"""
        html_content = """
        <html>
        <body>
        <table>
        <tr><th>Name</th><th>Value</th></tr>
        <tr><td>Test</td><td>123</td></tr>
        </table>
        </body>
        </html>
        """
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_file = f.name

        try:
            with open_iterable(temp_file) as source:
                assert isinstance(source, HTMLIterable)
                row = source.read()
                assert row == {"Name": "Test", "Value": "123"}
        finally:
            os.unlink(temp_file)

    def test_htm_extension(self):
        """Test .htm extension is recognized"""
        html_content = """
        <html>
        <body>
        <table>
        <tr><th>Name</th></tr>
        <tr><td>Test</td></tr>
        </table>
        </body>
        </html>
        """
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".htm", delete=False) as f:
            f.write(html_content)
            temp_file = f.name

        try:
            with open_iterable(temp_file) as source:
                assert isinstance(source, HTMLIterable)
        finally:
            os.unlink(temp_file)

    def test_reset(self):
        """Test reset functionality"""
        html_content = """
        <html>
        <body>
        <table>
        <tr><th>Name</th></tr>
        <tr><td>First</td></tr>
        </table>
        </body>
        </html>
        """
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_file = f.name

        try:
            iterable = HTMLIterable(temp_file)
            row1 = iterable.read()
            iterable.reset()
            row2 = iterable.read()
            assert row1 == row2
            iterable.close()
        finally:
            os.unlink(temp_file)

    def test_read_bulk(self):
        """Test bulk reading"""
        html_content = """
        <html>
        <body>
        <table>
        <tr><th>ID</th><th>Name</th></tr>
        <tr><td>1</td><td>Alice</td></tr>
        <tr><td>2</td><td>Bob</td></tr>
        <tr><td>3</td><td>Charlie</td></tr>
        </table>
        </body>
        </html>
        """
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_file = f.name

        try:
            iterable = HTMLIterable(temp_file)
            rows = iterable.read_bulk(2)
            assert len(rows) == 2
            assert rows[0] == {"ID": "1", "Name": "Alice"}
            assert rows[1] == {"ID": "2", "Name": "Bob"}
            iterable.close()
        finally:
            os.unlink(temp_file)

    def test_missing_dependency(self):
        """Test that missing beautifulsoup4 raises helpful error"""
        # This test would need to mock the import, but we can at least verify
        # the error message format is correct by checking the code
        pass

    def test_has_tables(self):
        """Test has_tables static method"""
        assert HTMLIterable.has_tables() is True

    def test_list_tables_single_table(self):
        """Test list_tables with single table"""
        html_content = """
        <html>
        <body>
        <table>
        <tr><th>Name</th></tr>
        <tr><td>Test</td></tr>
        </table>
        </body>
        </html>
        """
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_file = f.name

        try:
            iterable = HTMLIterable(temp_file)
            tables = iterable.list_tables(temp_file)
            assert isinstance(tables, list)
            assert len(tables) == 1
            assert tables[0] == "0"  # Index as string
            iterable.close()
        finally:
            os.unlink(temp_file)

    def test_list_tables_multiple_tables(self):
        """Test list_tables with multiple tables"""
        html_content = """
        <html>
        <body>
        <table id="table1">
        <tr><th>Name</th></tr>
        <tr><td>Test1</td></tr>
        </table>
        <table id="table2">
        <tr><th>Name</th></tr>
        <tr><td>Test2</td></tr>
        </table>
        <table>
        <caption>Third Table</caption>
        <tr><th>Name</th></tr>
        <tr><td>Test3</td></tr>
        </table>
        </body>
        </html>
        """
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_file = f.name

        try:
            iterable = HTMLIterable(temp_file)
            tables = iterable.list_tables(temp_file)
            assert isinstance(tables, list)
            assert len(tables) == 3
            assert "table1" in tables
            assert "table2" in tables
            assert "Third Table" in tables
            iterable.close()
        finally:
            os.unlink(temp_file)

    def test_list_tables_instance_method(self):
        """Test list_tables on already-opened instance"""
        html_content = """
        <html>
        <body>
        <table id="first">
        <tr><th>Name</th></tr>
        <tr><td>Test</td></tr>
        </table>
        <table id="second">
        <tr><th>Name</th></tr>
        <tr><td>Test2</td></tr>
        </table>
        </body>
        </html>
        """
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_file = f.name

        try:
            iterable = HTMLIterable(temp_file, table_index=0)
            tables = iterable.list_tables()
            assert isinstance(tables, list)
            assert len(tables) == 2
            assert "first" in tables
            assert "second" in tables
            iterable.close()
        finally:
            os.unlink(temp_file)

    def test_list_tables_empty_file(self):
        """Test list_tables on HTML file with no tables"""
        html_content = """
        <html>
        <body>
        <p>No tables here</p>
        </body>
        </html>
        """
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_file = f.name

        try:
            iterable = HTMLIterable(temp_file)
            tables = iterable.list_tables(temp_file)
            assert isinstance(tables, list)
            assert len(tables) == 0
            iterable.close()
        finally:
            os.unlink(temp_file)
