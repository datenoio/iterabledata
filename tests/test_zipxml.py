import zipfile

import pytest

pytest.importorskip("lxml", reason="lxml is required for ZIP-XML support")

from iterable.datatypes import ZIPXMLSource  # noqa: E402

GOLDEN_ZIPXML = "fixtures/test_zipxml.zip"


class TestZIPXML:
    def test_id(self):
        source = ZIPXMLSource(GOLDEN_ZIPXML, tagname="item")
        datatype_id = source.id()
        assert datatype_id == "zip-xml"
        source.close()

    def test_is_flat(self):
        source = ZIPXMLSource(GOLDEN_ZIPXML, tagname="item")
        flag = source.is_flat()
        assert not flag
        source.close()

    def test_openclose(self, tmp_path):
        """Test basic open/close"""
        test_file = tmp_path / "test.zip"
        with zipfile.ZipFile(test_file, "w") as zf:
            zf.writestr("data.xml", '<?xml version="1.0"?><root><item>test</item></root>')

        source = ZIPXMLSource(str(test_file), tagname="item")
        source.close()

    def test_read_one(self, tmp_path):
        """Test reading single XML record from ZIP"""
        test_file = tmp_path / "test.zip"
        with zipfile.ZipFile(test_file, "w") as zf:
            zf.writestr("data.xml", '<?xml version="1.0"?><root><item><name>test</name></item></root>')

        source = ZIPXMLSource(str(test_file), tagname="item")
        try:
            record = source.read()
            assert isinstance(record, dict)
        except NotImplementedError:
            pass
        source.close()

    def test_iterfile(self, tmp_path):
        """Test iterating through files in ZIP"""
        test_file = tmp_path / "test.zip"
        with zipfile.ZipFile(test_file, "w") as zf:
            zf.writestr("file1.xml", '<?xml version="1.0"?><root><item>1</item></root>')
            zf.writestr("file2.xml", '<?xml version="1.0"?><root><item>2</item></root>')

        source = ZIPXMLSource(str(test_file), tagname="item")
        has_more = source.iterfile()
        assert isinstance(has_more, bool)
        source.close()

    def test_real_data(self):
        """Test with provided real-world ZIP file"""
        source = ZIPXMLSource(GOLDEN_ZIPXML, tagname="Документ")
        count = 0
        for record in source:
            assert isinstance(record, dict)
            assert "@ИдДок" in record
            count += 1

        assert count > 0
        source.close()

    def test_has_tables(self):
        """Test has_tables static method"""
        assert ZIPXMLSource.has_tables() is True

    def test_list_tables_single_xml(self, tmp_path):
        """Test list_tables with single XML file"""
        test_file = tmp_path / "test.zip"
        with zipfile.ZipFile(test_file, "w") as zf:
            zf.writestr("data.xml", '<?xml version="1.0"?><root><item>test</item></root>')

        source = ZIPXMLSource(str(test_file), tagname="item")
        tables = source.list_tables(str(test_file))
        assert isinstance(tables, list)
        assert len(tables) == 1
        assert "data.xml" in tables
        source.close()

    def test_list_tables_multiple_xml(self, tmp_path):
        """Test list_tables with multiple XML files"""
        test_file = tmp_path / "test.zip"
        with zipfile.ZipFile(test_file, "w") as zf:
            zf.writestr("file1.xml", '<?xml version="1.0"?><root><item>1</item></root>')
            zf.writestr("file2.xml", '<?xml version="1.0"?><root><item>2</item></root>')
            zf.writestr("file3.xml", '<?xml version="1.0"?><root><item>3</item></root>')
            zf.writestr("readme.txt", "Not an XML file")

        source = ZIPXMLSource(str(test_file), tagname="item")
        tables = source.list_tables(str(test_file))
        assert isinstance(tables, list)
        assert len(tables) == 3
        assert "file1.xml" in tables
        assert "file2.xml" in tables
        assert "file3.xml" in tables
        assert "readme.txt" not in tables
        source.close()

    def test_list_tables_instance_method(self, tmp_path):
        """Test list_tables on already-opened instance"""
        test_file = tmp_path / "test.zip"
        with zipfile.ZipFile(test_file, "w") as zf:
            zf.writestr("first.xml", '<?xml version="1.0"?><root><item>1</item></root>')
            zf.writestr("second.xml", '<?xml version="1.0"?><root><item>2</item></root>')

        source = ZIPXMLSource(str(test_file), tagname="item")
        tables = source.list_tables()
        assert isinstance(tables, list)
        assert len(tables) == 2
        assert "first.xml" in tables
        assert "second.xml" in tables
        source.close()

    def test_list_tables_empty_zip(self, tmp_path):
        """Test list_tables on ZIP file with no XML files"""
        test_file = tmp_path / "test.zip"
        with zipfile.ZipFile(test_file, "w") as zf:
            zf.writestr("readme.txt", "No XML here")
            zf.writestr("data.json", '{"key": "value"}')

        source = ZIPXMLSource(str(test_file), tagname="item")
        tables = source.list_tables(str(test_file))
        assert isinstance(tables, list)
        assert len(tables) == 0
        source.close()
