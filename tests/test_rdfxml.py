import os

import pytest

pytest.importorskip("lxml", reason="lxml is required for RDF/XML support")

from iterable.datatypes import RDFXMLIterable  # noqa: E402


class TestRDFXML:
    def test_id(self):
        datatype_id = RDFXMLIterable.id()
        assert datatype_id == "rdfxml"

    def test_flatonly(self):
        flag = RDFXMLIterable.is_flatonly()
        assert not flag

    def test_openclose(self):
        """Test basic open/close"""
        test_file = "testdata/test_rdfxml.rdf"
        os.makedirs("testdata", exist_ok=True)
        with open(test_file, "w") as f:
            f.write('<?xml version="1.0"?>\n')
            f.write('<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n')
            f.write('  <rdf:Description rdf:about="http://example.com/subject">\n')
            f.write('    <rdf:type rdf:resource="http://example.com/Type"/>\n')
            f.write("  </rdf:Description>\n")
            f.write("</rdf:RDF>\n")

        iterable = RDFXMLIterable(test_file)
        iterable.close()

        if os.path.exists(test_file):
            os.unlink(test_file)

    def test_read_one(self):
        """Test reading single RDF/XML record"""
        test_file = "testdata/test_rdfxml_read.rdf"
        os.makedirs("testdata", exist_ok=True)
        with open(test_file, "w") as f:
            f.write('<?xml version="1.0"?>\n')
            f.write('<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n')
            f.write('  <rdf:Description rdf:about="http://example.com/subject">\n')
            f.write('    <rdf:type rdf:resource="http://example.com/Type"/>\n')
            f.write("  </rdf:Description>\n")
            f.write("</rdf:RDF>\n")

        iterable = RDFXMLIterable(test_file)
        record = iterable.read()
        assert isinstance(record, dict)
        assert "subject" in record or "predicate" in record
        iterable.close()

        if os.path.exists(test_file):
            os.unlink(test_file)

    def test_read_bulk(self):
        """Test reading bulk RDF/XML records"""
        test_file = "testdata/test_rdfxml_bulk.rdf"
        os.makedirs("testdata", exist_ok=True)
        with open(test_file, "w") as f:
            f.write('<?xml version="1.0"?>\n')
            f.write('<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n')
            f.write('  <rdf:Description rdf:about="http://example.com/subject1">\n')
            f.write('    <rdf:type rdf:resource="http://example.com/Type"/>\n')
            f.write("  </rdf:Description>\n")
            f.write('  <rdf:Description rdf:about="http://example.com/subject2">\n')
            f.write('    <rdf:type rdf:resource="http://example.com/Type"/>\n')
            f.write("  </rdf:Description>\n")
            f.write("</rdf:RDF>\n")

        iterable = RDFXMLIterable(test_file)
        chunk = iterable.read_bulk(2)
        assert isinstance(chunk, list)
        assert len(chunk) > 0
        iterable.close()

        if os.path.exists(test_file):
            os.unlink(test_file)

    def test_reset(self):
        """Test reset functionality"""
        test_file = "testdata/test_rdfxml_reset.rdf"
        os.makedirs("testdata", exist_ok=True)
        with open(test_file, "w") as f:
            f.write('<?xml version="1.0"?>\n')
            f.write('<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n')
            f.write('  <rdf:Description rdf:about="http://example.com/subject">\n')
            f.write('    <rdf:type rdf:resource="http://example.com/Type"/>\n')
            f.write("  </rdf:Description>\n")
            f.write("</rdf:RDF>\n")

        iterable = RDFXMLIterable(test_file)
        record1 = iterable.read()
        iterable.reset()
        record2 = iterable.read()
        assert record1 == record2
        iterable.close()

        if os.path.exists(test_file):
            os.unlink(test_file)
