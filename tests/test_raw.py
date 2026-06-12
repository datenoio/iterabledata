import os

from fixdata import FIXTURES

from iterable.codecs import RAWCodec
from iterable.datatypes import CSVIterable


class TestRAW:
    def test_id(self):
        codec_id = RAWCodec.id()
        assert codec_id == "raw"

    def test_fileexts(self):
        """Test fileexts method"""
        exts = RAWCodec.fileexts()
        # RAW codec returns empty list (no specific extensions)
        assert exts == []

    def test_openclose(self):
        """Test basic open/close"""
        codec = RAWCodec("fixtures/2cols6rows.csv", mode="r", open_it=True)
        assert codec._fileobj is not None
        codec.close()
        assert codec._fileobj is None

    def test_open_read(self):
        """Test opening and reading through codec"""
        codec = RAWCodec("fixtures/2cols6rows.csv", mode="r", open_it=True)
        fileobj = codec.fileobj()
        assert fileobj is not None
        # Read first line
        line = fileobj.readline()
        assert line is not None
        codec.close()

    def test_open_write(self):
        """Test opening for writing"""
        test_file = "testdata/test_raw_write.txt"
        os.makedirs("testdata", exist_ok=True)

        codec = RAWCodec(test_file, mode="w", open_it=True)
        fileobj = codec.fileobj()
        fileobj.write("test content")
        codec.close()

        # Verify file was written
        assert os.path.exists(test_file)
        with open(test_file) as f:
            assert f.read() == "test content"

        if os.path.exists(test_file):
            os.unlink(test_file)

    def test_with_csv_iterable(self):
        """Test RAW codec with CSV iterable"""
        codec = RAWCodec("fixtures/2cols6rows.csv", mode="r", open_it=True)
        iterable = CSVIterable(codec=codec)
        row = iterable.read()
        assert row == FIXTURES[0]
        iterable.close()

    def test_reset(self):
        """Test reset functionality"""
        codec = RAWCodec("fixtures/2cols6rows.csv", mode="r", open_it=True)
        fileobj1 = codec.fileobj()
        codec.reset()
        fileobj2 = codec.fileobj()
        # After reset, should have a new file object
        assert fileobj1 is not None
        assert fileobj2 is not None
        codec.close()

    def test_fileobj(self):
        """Test fileobj() method"""
        codec = RAWCodec("fixtures/2cols6rows.csv", mode="r", open_it=True)
        fileobj = codec.fileobj()
        assert fileobj is not None
        assert hasattr(fileobj, "read")
        codec.close()
