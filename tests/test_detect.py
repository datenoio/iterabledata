import pytest

from iterable.codecs import BZIP2Codec, GZIPCodec, LZMACodec

# Optional codecs - may not be available
try:
    from iterable.codecs import BrotliCodec
# noqa: F401
except (ImportError, NameError):
    BrotliCodec = None

try:
    from iterable.codecs import ZSTDCodec
# noqa: F401
except (ImportError, NameError):
    ZSTDCodec = None
from iterable.datatypes import (
    CSVIterable,
    JSONIterable,
    JSONLinesIterable,
    PickleIterable,
)

# Optional datatypes - may not be available
try:
    from iterable.datatypes import AVROIterable
# noqa: F401
except (ImportError, NameError):
    AVROIterable = None

try:
    from iterable.datatypes import BSONIterable
# noqa: F401
except (ImportError, NameError):
    BSONIterable = None

try:
    from iterable.datatypes import DBFIterable
# noqa: F401
except (ImportError, NameError):
    DBFIterable = None

try:
    from iterable.datatypes import DuckDBIterable
# noqa: F401
except (ImportError, NameError):
    DuckDBIterable = None

try:
    from iterable.datatypes import ORCIterable
# noqa: F401
except (ImportError, NameError):
    ORCIterable = None

try:
    from iterable.datatypes import ParquetIterable
# noqa: F401
except (ImportError, NameError):
    ParquetIterable = None

try:
    from iterable.datatypes import XLSIterable
# noqa: F401
except (ImportError, NameError):
    XLSIterable = None

try:
    from iterable.datatypes import XLSXIterable
# noqa: F401
except (ImportError, NameError):
    XLSXIterable = None

try:
    from iterable.datatypes import XMLIterable
# noqa: F401
except (ImportError, NameError):
    XMLIterable = None
from iterable.helpers.detect import detect_encoding_any, detect_file_type
from iterable.helpers.utils import detect_delimiter, detect_encoding_raw


class TestDetectors:
    def test_encoding(self):
        assert detect_encoding_raw(filename="fixtures/ru_utf8_comma.csv")["encoding"].lower() == "utf-8"
        assert detect_encoding_raw(filename="fixtures/ru_cp1251_comma.csv")["encoding"].lower() == "windows-1251"

    def test_encoding_any_raw(self):
        assert detect_encoding_any(filename="fixtures/ru_utf8_comma.csv")["encoding"].lower() == "utf-8"
        assert detect_encoding_any(filename="fixtures/ru_cp1251_comma.csv")["encoding"].lower() == "windows-1251"

    def test_encoding_any_compressed(self):
        #        assert 'utf-8' == detect_encoding_any(filename='fixtures/ru_utf8_comma.csv.zst')['encoding']
        assert detect_encoding_any(filename="fixtures/ru_cp1251_comma.csv.gz")["encoding"].lower() == "windows-1251"

    def test_delimiters(self):
        assert "," == detect_delimiter(filename="fixtures/ru_utf8_comma.csv")
        assert ";" == detect_delimiter(filename="fixtures/ru_utf8_semicolon.csv")
        assert "\t" == detect_delimiter(filename="fixtures/ru_utf8_tab.csv")

    def test_filetype_csv_utf8(self):
        result = detect_file_type("fixtures/9_25.24.28.712_2014.csv")
        assert result["success"]
        assert result["datatype"] == CSVIterable
        assert result["codec"] is None

    def test_filetype_plain_csv(self):
        result = detect_file_type("fixtures/ru_utf8_comma.csv")
        assert result["success"]
        assert result["datatype"] == CSVIterable
        assert result["codec"] is None

    def test_filetype_bson(self):
        if BSONIterable is None:
            pytest.skip("bson extra not installed")
        result = detect_file_type("fixtures/2cols6rows_flat.bson")
        assert result["success"]
        assert result["datatype"] == BSONIterable
        assert result["codec"] is None

    def test_filetype_pickle(self):
        result = detect_file_type("fixtures/2cols6rows_flat.pickle")
        assert result["success"]
        assert result["datatype"] == PickleIterable
        assert result["codec"] is None

    def test_filetype_json(self):
        result = detect_file_type("fixtures/2cols6rows_array.json")
        assert result["success"]
        assert result["datatype"] == JSONIterable
        assert result["codec"] is None

    def test_filetype_jsonl(self):
        result = detect_file_type("fixtures/2cols6rows_flat.jsonl")
        assert result["success"]
        assert result["datatype"] == JSONLinesIterable
        assert result["codec"] is None

    def test_filetype_ndjson(self):
        result = detect_file_type("fixtures/2cols6rows_flat.ndjson")
        assert result["success"]
        assert result["datatype"] == JSONLinesIterable
        assert result["codec"] is None

    def test_filetype_avro(self):
        if AVROIterable is None:
            pytest.skip("avro extra not installed")
        result = detect_file_type("fixtures/2cols6rows.avro")
        assert result["success"]
        assert result["datatype"] == AVROIterable
        assert result["codec"] is None

    def test_filetype_orc(self):
        if ORCIterable is None:
            pytest.skip("pyorc is required for ORC support")
        result = detect_file_type("fixtures/2cols6rows.orc")
        assert result["success"]
        assert result["datatype"] == ORCIterable
        assert result["codec"] is None

    def test_filetype_xml(self):
        if XMLIterable is None:
            pytest.skip("xml extra not installed")
        result = detect_file_type("fixtures/books.xml")
        assert result["success"]
        assert result["datatype"] == XMLIterable
        assert result["codec"] is None

    def test_filetype_zstd_csv(self):
        if ZSTDCodec is None:
            pytest.skip("ZSTDCodec not available")
        result = detect_file_type("fixtures/2cols6rows.csv.zst")
        assert result["success"]
        assert result["datatype"] == CSVIterable
        assert result["codec"] == ZSTDCodec

    def test_filetype_brotli_csv(self):
        if BrotliCodec is None:
            pytest.skip("BrotliCodec not available")
        result = detect_file_type("fixtures/2cols6rows.csv.br")
        assert result["success"]
        assert result["datatype"] == CSVIterable
        assert result["codec"] == BrotliCodec

    def test_filetype_bzip2_csv(self):
        result = detect_file_type("fixtures/2cols6rows.csv.bz2")
        assert result["success"]
        assert result["datatype"] == CSVIterable
        assert result["codec"] == BZIP2Codec

    def test_filetype_lzma_csv(self):
        result = detect_file_type("fixtures/2cols6rows.csv.xz")
        assert result["success"]
        assert result["datatype"] == CSVIterable
        assert result["codec"] == LZMACodec

    def test_filetype_gzip_csv(self):
        result = detect_file_type("fixtures/2cols6rows.csv.gz")
        assert result["success"]
        assert result["datatype"] == CSVIterable
        assert result["codec"] == GZIPCodec

    def test_filetype_plain_parquet(self):
        if ParquetIterable is None:
            pytest.skip("pyarrow is required for Parquet support")
        result = detect_file_type("fixtures/2cols6rows.parquet")
        assert result["success"]
        assert result["datatype"] == ParquetIterable
        assert result["codec"] is None

    def test_filetype_plain_xls(self):
        if XLSIterable is None:
            pytest.skip("excel extra not installed")
        result = detect_file_type("fixtures/2cols6rows.xls")
        assert result["success"]
        assert result["datatype"] == XLSIterable
        assert result["codec"] is None

    def test_filetype_plain_xlsx(self):
        if XLSXIterable is None:
            pytest.skip("excel extra not installed")
        result = detect_file_type("fixtures/2cols6rows.xlsx")
        assert result["success"]
        assert result["datatype"] == XLSXIterable
        assert result["codec"] is None

    def test_filetype_plain_dbf(self):
        if DBFIterable is None:
            pytest.skip("dbfread is required for DBF support")
        result = detect_file_type("fixtures/2cols6rows.dbf")
        assert result["success"]
        assert result["datatype"] == DBFIterable
        assert result["codec"] is None

    def test_filetype_duckdb(self):
        """Test DuckDB format detection"""
        import tempfile

        duckdb = pytest.importorskip("duckdb", reason="duckdb is required for DuckDB detection")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".duckdb") as tmp:
            tmp_path = tmp.name
        # DuckDB may error if the file already exists but is empty/not a valid DB.
        # Ensure the path does not exist before connecting so DuckDB can create it.
        import os

        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

        try:
            # Create a minimal DuckDB database file
            conn = duckdb.connect(tmp_path)
            conn.execute("CREATE TABLE test (id INTEGER)")
            if hasattr(conn, "commit"):
                conn.commit()
            conn.close()

            result = detect_file_type(tmp_path)
            assert result["success"]
            assert result["datatype"] == DuckDBIterable
            assert result["codec"] is None
        finally:
            import os

            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_filetype_ddb(self):
        """Test DuckDB format detection with .ddb extension"""
        import tempfile

        duckdb = pytest.importorskip("duckdb", reason="duckdb is required for DuckDB detection")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".ddb") as tmp:
            tmp_path = tmp.name
        # DuckDB may error if the file already exists but is empty/not a valid DB.
        # Ensure the path does not exist before connecting so DuckDB can create it.
        import os

        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

        try:
            # Create a minimal DuckDB database file
            conn = duckdb.connect(tmp_path)
            conn.execute("CREATE TABLE test (id INTEGER)")
            if hasattr(conn, "commit"):
                conn.commit()
            conn.close()

            result = detect_file_type(tmp_path)
            assert result["success"]
            assert result["datatype"] == DuckDBIterable
            assert result["codec"] is None
        finally:
            import os

            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_detect_file_type_empty_filename(self):
        """Test detect_file_type with empty filename raises ValueError"""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            detect_file_type("")

    def test_detect_file_type_unknown_format(self):
        """Test detect_file_type with unknown format"""
        result = detect_file_type("test.unknown")
        assert result["success"] is False
        assert result["datatype"] is None
        assert result["codec"] is None

    def test_detect_file_type_no_extension(self):
        """Test detect_file_type with no extension"""
        result = detect_file_type("test")
        assert result["success"] is False

    def test_detect_compression_empty_filename(self):
        """Test detect_compression with empty filename raises ValueError"""
        from iterable.helpers.detect import detect_compression

        with pytest.raises(ValueError, match="Filename cannot be empty"):
            detect_compression("")

    def test_detect_compression_gzip(self):
        """Test detect_compression with gzip file"""
        from iterable.helpers.detect import detect_compression

        result = detect_compression("test.csv.gz")
        assert result["success"] is True
        assert result["compression"] == GZIPCodec
        assert result["codec"] is None
        assert result["datatype"] is None

    def test_detect_compression_bz2(self):
        """Test detect_compression with bz2 file"""
        from iterable.helpers.detect import detect_compression

        result = detect_compression("test.bz2")
        assert result["success"] is True
        assert result["compression"] == BZIP2Codec

    def test_detect_compression_no_compression(self):
        """Test detect_compression with no compression"""
        from iterable.helpers.detect import detect_compression

        result = detect_compression("test.csv")
        assert result["success"] is False
        assert result["compression"] is None

    def test_detect_encoding_any_empty_filename(self):
        """Test detect_encoding_any with empty filename raises ValueError"""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            detect_encoding_any("")

    def test_detect_encoding_any_file_not_found(self):
        """Test detect_encoding_any with non-existent file raises FileNotFoundError"""
        import os

        non_existent = "this_file_does_not_exist_12345.txt"
        assert not os.path.exists(non_existent)
        with pytest.raises(FileNotFoundError):
            detect_encoding_any(non_existent)

    def test_detect_encoding_any_empty_file(self, tmp_path):
        """Test detect_encoding_any with empty file raises ValueError"""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        with pytest.raises(ValueError, match="appears to be empty"):
            detect_encoding_any(str(empty_file))

    def test_open_iterable_empty_filename(self):
        """Test open_iterable with empty filename raises ValueError"""
        from iterable.helpers.detect import open_iterable

        with pytest.raises(ValueError, match="Filename cannot be empty"):
            open_iterable("")

    def test_open_iterable_invalid_engine(self):
        """Test open_iterable with invalid engine raises ValueError"""
        from iterable.helpers.detect import open_iterable

        with pytest.raises(ValueError, match="Engine must be 'internal', 'duckdb'"):
            open_iterable("test.csv", engine="invalid")

    def test_open_iterable_file_not_found(self):
        """Test open_iterable with non-existent file raises FileNotFoundError"""
        import os

        from iterable.helpers.detect import open_iterable

        non_existent = "this_file_does_not_exist_12345.csv"
        assert not os.path.exists(non_existent)
        with pytest.raises(FileNotFoundError):
            open_iterable(non_existent)

    def test_open_iterable_unknown_format(self, tmp_path):
        """Test open_iterable with unknown format raises RuntimeError"""
        from iterable.helpers.detect import open_iterable

        unknown_file = tmp_path / "test.unknown"
        unknown_file.write_text("test data")

        with pytest.raises(RuntimeError, match="Could not detect file type"):
            open_iterable(str(unknown_file))

    def test_open_iterable_duckdb_unsupported_format(self, tmp_path):
        """Test open_iterable with DuckDB engine and unsupported format"""
        from iterable.helpers.detect import open_iterable

        xml_file = tmp_path / "test.xml"
        xml_file.write_text("<root><item>test</item></root>")

        with pytest.raises(ValueError, match="DuckDB engine does not support file type"):
            open_iterable(str(xml_file), engine="duckdb")

    def test_is_flat_function(self):
        """Test is_flat function"""
        from iterable.helpers.detect import is_flat

        # Test with filename
        assert is_flat(filename="test.csv") is True
        assert is_flat(filename="test.json") is False
        # Test with filetype
        assert is_flat(filetype="csv") is True
        assert is_flat(filetype="json") is False
        # Test with None
        assert is_flat() is False

    def test_is_flat_with_compressed(self):
        """Test is_flat with compressed file"""
        from iterable.helpers.detect import is_flat

        assert is_flat(filename="test.csv.gz") is True
        assert is_flat(filename="test.json.gz") is False

    def test_open_iterable_basic(self):
        """Test open_iterable with basic file"""
        from iterable.helpers.detect import open_iterable

        iterable = open_iterable("fixtures/2cols6rows.csv")
        assert iterable is not None
        iterable.close()

    def test_open_iterable_with_mode(self):
        """Test open_iterable with write mode"""
        import os

        from iterable.helpers.detect import open_iterable

        os.makedirs("testdata", exist_ok=True)
        iterable = open_iterable("testdata/test_open_write.csv", mode="w")
        assert iterable is not None
        iterable.close()
        if os.path.exists("testdata/test_open_write.csv"):
            os.unlink("testdata/test_open_write.csv")

    def test_open_iterable_with_iterableargs(self):
        """Test open_iterable with iterableargs"""
        from iterable.helpers.detect import open_iterable

        iterable = open_iterable("fixtures/ru_utf8_semicolon.csv", iterableargs={"delimiter": ";"})
        assert iterable is not None
        row = iterable.read()
        assert row is not None
        iterable.close()

    def test_open_iterable_unknown_format_string(self):
        """Test open_iterable with unknown format string path"""
        from iterable.helpers.detect import open_iterable

        with pytest.raises((ValueError, ImportError)):
            open_iterable("test.unknown_format_xyz")

    def test_detect_file_type_from_content(self, tmp_path):
        """Test detect_file_type_from_content with various formats"""
        from iterable.helpers.detect import detect_file_type_from_content

        # Test JSON detection
        json_file = tmp_path / "test.json"
        json_file.write_text('{"name": "test"}')
        with open(json_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "json"
        assert 0.8 <= confidence <= 1.0
        assert method == "heuristic"

        # Test CSV detection
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,name\n1,test")
        with open(csv_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id in ["csv", "tsv"]  # May detect as CSV or TSV
        assert 0.7 <= confidence <= 1.0
        assert method == "heuristic"

    def test_detect_file_type_empty_filename_string(self):
        """Test detect_file_type with empty filename raises ValueError"""
        from iterable.helpers.detect import detect_file_type

        with pytest.raises(ValueError, match="Filename cannot be empty"):
            detect_file_type("")

    def test_detect_file_type_with_fileobj(self, tmp_path):
        """Test detect_file_type with fileobj"""
        from iterable.helpers.detect import detect_file_type

        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,name\n1,test")
        with open(csv_file, "rb") as f:
            result = detect_file_type(str(csv_file), fileobj=f)
        assert result["success"]
        assert result["datatype"] == CSVIterable
        assert "confidence" in result
        assert result["confidence"] == 1.0  # Filename detection has highest confidence
        assert result["detection_method"] == "filename"

    def test_load_symbol_error_handling(self):
        """Test _load_symbol error handling"""
        from iterable.helpers.detect import _load_symbol

        # Test with invalid module
        with pytest.raises(ImportError):
            _load_symbol("nonexistent.module", "NonExistentClass")

    def test_datatype_class(self):
        """Test _datatype_class function"""
        from iterable.helpers.detect import _datatype_class

        csv_class = _datatype_class("csv")
        assert csv_class == CSVIterable

    def test_codec_class(self):
        """Test _codec_class function"""
        from iterable.helpers.detect import _codec_class

        gzip_class = _codec_class("gz")
        assert gzip_class == GZIPCodec

    def test_detect_compression_unknown(self):
        """Test detect_compression with unknown format"""
        from iterable.helpers.detect import detect_compression

        result = detect_compression("test.unknown")
        assert result["success"] is False
        assert result["compression"] is None

    def test_detect_encoding_any_with_limit(self, tmp_path):
        """Test detect_encoding_any with custom limit"""
        from iterable.helpers.detect import detect_encoding_any

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content" * 1000)
        result = detect_encoding_any(str(test_file), limit=100)
        assert "encoding" in result


class TestConfidenceScores:
    """Test confidence scores in detection results."""

    def test_filename_detection_confidence(self, tmp_path):
        """Test that filename detection has highest confidence."""
        from iterable.helpers.detect import detect_file_type

        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,name\n1,test")
        result = detect_file_type(str(csv_file))
        assert result["success"]
        assert result["confidence"] == 1.0
        assert result["detection_method"] == "filename"

    def test_magic_number_confidence(self, tmp_path):
        """Test that magic number detection has high confidence."""
        pytest.importorskip("pyarrow", reason="pyarrow is required to resolve the Parquet class")
        from iterable.helpers.detect import detect_file_type

        parquet_file = tmp_path / "data"
        parquet_file.write_bytes(b"PAR1" + b"\x00" * 100)
        with open(parquet_file, "rb") as f:
            result = detect_file_type(str(parquet_file), fileobj=f)
        assert result["success"]
        assert result["confidence"] >= 0.95
        assert result["detection_method"] == "magic_number"

    def test_heuristic_confidence(self, tmp_path):
        """Test that heuristic detection has medium confidence."""
        from iterable.helpers.detect import detect_file_type

        json_file = tmp_path / "data"
        json_file.write_text('{"name": "test"}')
        with open(json_file, "rb") as f:
            result = detect_file_type(str(json_file), fileobj=f)
        assert result["success"]
        assert 0.7 <= result["confidence"] <= 0.95
        assert result["detection_method"] == "heuristic"


class TestContentBasedDetection:
    """Test content-based format detection (magic numbers and heuristics)."""

    def test_magic_number_parquet(self, tmp_path):
        """Test Parquet magic number detection."""
        from iterable.helpers.detect import detect_file_type_from_content

        parquet_file = tmp_path / "test.parquet"
        parquet_file.write_bytes(b"PAR1" + b"\x00" * 100)
        with open(parquet_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "parquet"
        assert confidence >= 0.95
        assert method == "magic_number"

    def test_magic_number_orc(self, tmp_path):
        """Test ORC magic number detection."""
        from iterable.helpers.detect import detect_file_type_from_content

        orc_file = tmp_path / "test.orc"
        orc_file.write_bytes(b"ORC" + b"\x00" * 100)
        with open(orc_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "orc"
        assert confidence >= 0.95
        assert method == "magic_number"

    def test_magic_number_vortex(self, tmp_path):
        """Test Vortex magic number detection."""
        from iterable.helpers.detect import detect_file_type_from_content

        vortex_file = tmp_path / "test.vortex"
        vortex_file.write_bytes(b"VTXF" + b"\x00" * 100)
        with open(vortex_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "vortex"
        assert confidence >= 0.95
        assert method == "magic_number"

    def test_magic_number_pcap(self, tmp_path):
        """Test PCAP magic number detection."""
        from iterable.helpers.detect import detect_file_type_from_content

        # Little-endian PCAP
        pcap_le_file = tmp_path / "test_le.pcap"
        pcap_le_file.write_bytes(b"\xd4\xc3\xb2\xa1" + b"\x00" * 100)
        with open(pcap_le_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "pcap"
        assert confidence >= 0.95
        assert method == "magic_number"

        # Big-endian PCAP
        pcap_be_file = tmp_path / "test_be.pcap"
        pcap_be_file.write_bytes(b"\xa1\xb2\xc3\xd4" + b"\x00" * 100)
        with open(pcap_be_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "pcap"
        assert confidence >= 0.95
        assert method == "magic_number"

    def test_magic_number_pcapng(self, tmp_path):
        """Test PCAPNG magic number detection."""
        from iterable.helpers.detect import detect_file_type_from_content

        pcapng_file = tmp_path / "test.pcapng"
        pcapng_file.write_bytes(b"\x0a\x0d\x0d\x0a" + b"\x00" * 100)
        with open(pcapng_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "pcapng"
        assert confidence >= 0.95
        assert method == "magic_number"

    def test_magic_number_arrow(self, tmp_path):
        """Test Arrow/Feather magic number detection."""
        from iterable.helpers.detect import detect_file_type_from_content

        arrow_file = tmp_path / "test.arrow"
        arrow_file.write_bytes(b"ARROW1" + b"\x00" * 100)
        with open(arrow_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "arrow"
        assert confidence >= 0.95
        assert method == "magic_number"

    def test_magic_number_xlsx(self, tmp_path):
        """Test XLSX (ZIP-based) magic number detection."""
        from iterable.helpers.detect import detect_file_type_from_content

        # Create a minimal ZIP structure with xl/ directory indicator
        xlsx_file = tmp_path / "test.xlsx"
        xlsx_content = b"PK\x03\x04" + b"\x00" * 50 + b"xl/" + b"\x00" * 100
        xlsx_file.write_bytes(xlsx_content)
        with open(xlsx_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "xlsx"
        assert confidence >= 0.90
        assert method == "magic_number"

    def test_magic_number_zip(self, tmp_path):
        """Test generic ZIP magic number detection."""
        from iterable.helpers.detect import detect_file_type_from_content

        zip_file = tmp_path / "test.zip"
        zip_file.write_bytes(b"PK\x03\x04" + b"\x00" * 200)
        with open(zip_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "zip"
        assert confidence >= 0.85
        assert method == "magic_number"

    def test_json_detection(self, tmp_path):
        """Test JSON detection from content."""
        from iterable.helpers.detect import detect_file_type_from_content

        # JSON object
        json_obj_file = tmp_path / "test_obj.json"
        json_obj_file.write_text('{"name": "test", "value": 123}')
        with open(json_obj_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "json"
        assert 0.8 <= confidence <= 1.0
        assert method == "heuristic"

        # JSON array
        json_array_file = tmp_path / "test_array.json"
        json_array_file.write_text('[{"id": 1}, {"id": 2}]')
        with open(json_array_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "json"
        assert 0.8 <= confidence <= 1.0
        assert method == "heuristic"

    def test_jsonl_detection(self, tmp_path):
        """Test JSONL detection from content."""
        from iterable.helpers.detect import detect_file_type_from_content

        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"id": 1}\n{"id": 2}\n{"id": 3}\n')
        with open(jsonl_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "jsonl"
        assert 0.8 <= confidence <= 1.0
        assert method == "heuristic"

    def test_csv_detection(self, tmp_path):
        """Test CSV detection from content."""
        from iterable.helpers.detect import detect_file_type_from_content

        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,name,value\n1,test,123\n2,test2,456\n")
        with open(csv_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "csv"
        assert 0.7 <= confidence <= 1.0
        assert method == "heuristic"

    def test_tsv_detection(self, tmp_path):
        """Test TSV detection from content."""
        from iterable.helpers.detect import detect_file_type_from_content

        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text("id\tname\tvalue\n1\ttest\t123\n2\ttest2\t456\n")
        with open(tsv_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "tsv"
        assert 0.7 <= confidence <= 1.0
        assert method == "heuristic"

    def test_psv_detection(self, tmp_path):
        """Test PSV (pipe-separated) detection from content."""
        from iterable.helpers.detect import detect_file_type_from_content

        psv_file = tmp_path / "test.psv"
        psv_file.write_text("id|name|value\n1|test|123\n2|test2|456\n")
        with open(psv_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "psv"
        assert 0.7 <= confidence <= 1.0
        assert method == "heuristic"

    def test_empty_file(self, tmp_path):
        """Test detection with empty file."""
        from iterable.helpers.detect import detect_file_type_from_content

        empty_file = tmp_path / "empty.txt"
        empty_file.write_bytes(b"")
        with open(empty_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is None

    def test_binary_file_no_match(self, tmp_path):
        """Test detection with binary file that doesn't match any magic number."""
        from iterable.helpers.detect import detect_file_type_from_content

        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03" * 100)
        with open(binary_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is None

    def test_detect_file_type_with_content_fallback(self, tmp_path):
        """Test detect_file_type uses content detection when filename fails."""
        from iterable.helpers.detect import detect_file_type

        # File without extension but with JSON content
        json_file = tmp_path / "data"
        json_file.write_text('{"name": "test"}')
        with open(json_file, "rb") as f:
            result = detect_file_type(str(json_file), fileobj=f)
        assert result["success"]
        assert result["datatype"] == JSONIterable
        assert "confidence" in result
        assert 0.8 <= result["confidence"] <= 1.0
        assert result["detection_method"] == "heuristic"

    def test_detect_file_type_content_priority(self, tmp_path):
        """Test that filename detection takes priority over content detection."""
        from iterable.helpers.detect import detect_file_type

        # CSV file with JSON-like content (should detect as CSV from filename)
        csv_file = tmp_path / "test.csv"
        csv_file.write_text('{"name": "test"}')  # JSON-like but filename says CSV
        result = detect_file_type(str(csv_file))
        assert result["success"]
        assert result["datatype"] == CSVIterable
        assert result["confidence"] == 1.0  # Filename detection has highest confidence
        assert result["detection_method"] == "filename"

    def test_content_detection_preserves_file_position(self, tmp_path):
        """Test that content detection preserves file position."""
        from iterable.helpers.detect import detect_file_type_from_content

        json_file = tmp_path / "test.json"
        json_file.write_text('{"name": "test"}')
        with open(json_file, "rb") as f:
            initial_pos = f.tell()
            result = detect_file_type_from_content(f)
            final_pos = f.tell()
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "json"
        assert initial_pos == final_pos

    def test_jsonl_minimum_lines(self, tmp_path):
        """Test JSONL detection requires minimum number of valid lines."""
        from iterable.helpers.detect import detect_file_type_from_content

        # Only 2 valid JSON lines (should not be enough)
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"id": 1}\n{"id": 2}\n')
        with open(jsonl_file, "rb") as f:
            result = detect_file_type_from_content(f)
        # Should detect as JSONL if it has at least 3 lines, otherwise might detect as JSON
        if result is not None:
            format_id, confidence, method = result
            assert format_id in ["jsonl", "json"]
            assert method == "heuristic"

        # 3+ valid JSON lines (should detect as JSONL)
        jsonl_file.write_text('{"id": 1}\n{"id": 2}\n{"id": 3}\n{"id": 4}\n')
        with open(jsonl_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "jsonl"
        assert method == "heuristic"

    def test_csv_delimiter_consistency(self, tmp_path):
        """Test CSV detection checks for delimiter consistency."""
        from iterable.helpers.detect import detect_file_type_from_content

        # Inconsistent delimiter (should not detect as CSV)
        inconsistent_file = tmp_path / "test.txt"
        inconsistent_file.write_text("id,name,value\n1,test\n2,test2,value2,extra\n")
        with open(inconsistent_file, "rb") as f:
            result = detect_file_type_from_content(f)
        # May or may not detect as CSV depending on heuristics
        if result is not None:
            format_id, confidence, method = result
            assert format_id == "csv"
            assert method == "heuristic"
        # else: None is acceptable for inconsistent delimiters

        # Consistent delimiter (should detect as CSV)
        consistent_file = tmp_path / "test.csv"
        consistent_file.write_text("id,name,value\n1,test,123\n2,test2,456\n")
        with open(consistent_file, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        format_id, confidence, method = result
        assert format_id == "csv"
        assert method == "heuristic"
