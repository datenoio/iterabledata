"""Tests for iterable/base.py"""

import io

import pytest

from iterable.base import (
    DEFAULT_BULK_NUMBER,
    ITERABLE_TYPE_CODEC,
    ITERABLE_TYPE_FILE,
    ITERABLE_TYPE_STREAM,
    BaseCodec,
    BaseFileIterable,
    BaseIterable,
)
from iterable.exceptions import WriteNotSupportedError


class TestBaseCodec:
    """Test BaseCodec class"""

    def test_init_with_filename(self):
        """Test BaseCodec initialization with filename"""
        codec = BaseCodec(filename="test.txt")
        assert codec.filename == "test.txt"
        assert codec.mode == "r"
        assert codec._fileobj is None

    def test_init_with_fileobj(self):
        """Test BaseCodec initialization with file object"""
        fileobj = io.BytesIO(b"test data")
        codec = BaseCodec(fileobj=fileobj)
        assert codec._fileobj == fileobj
        assert codec.filename is None

    def test_init_with_mode(self):
        """Test BaseCodec initialization with mode"""
        codec = BaseCodec(filename="test.txt", mode="w")
        assert codec.mode == "w"

    def test_init_with_options(self):
        """Test BaseCodec initialization with options"""
        options = {"compression_level": 9, "custom_option": "value"}
        codec = BaseCodec(filename="test.txt", options=options)
        assert codec.compression_level == 9
        assert codec.custom_option == "value"

    def test_fileexts_not_implemented(self):
        """Test that fileexts raises NotImplementedError"""
        codec = BaseCodec()
        with pytest.raises(NotImplementedError):
            codec.fileexts()

    def test_open_not_implemented(self):
        """Test that open raises NotImplementedError"""
        codec = BaseCodec(filename="test.txt")
        with pytest.raises(NotImplementedError):
            codec.open()

    def test_close_not_implemented(self):
        """Test that close raises NotImplementedError"""
        codec = BaseCodec()
        with pytest.raises(NotImplementedError):
            codec.close()

    def test_fileobj(self):
        """Test fileobj method"""
        fileobj = io.BytesIO(b"test")
        codec = BaseCodec(fileobj=fileobj)
        assert codec.fileobj() == fileobj

    def test_reset(self):
        """Test reset method"""
        codec = BaseCodec(filename="test.txt")
        # Should call close and open, but will raise NotImplementedError
        with pytest.raises(NotImplementedError):
            codec.reset()

    def test_context_manager(self):
        """Test context manager protocol"""
        # This will fail because open() is not implemented
        codec = BaseCodec(filename="test.txt")
        with pytest.raises(NotImplementedError):
            with codec:
                pass

    def test_textIO(self):
        """Test textIO method"""
        fileobj = io.BytesIO(b"test")
        codec = BaseCodec(fileobj=fileobj)
        text_wrapper = codec.textIO(encoding="utf-8")
        assert isinstance(text_wrapper, io.TextIOWrapper)


class ConcreteIterable(BaseIterable):
    """Concrete implementation of BaseIterable for testing"""

    def __init__(self, data=None):
        super().__init__()
        self.data = data or []
        self.pos = 0

    @staticmethod
    def id():
        return "test"

    def reset(self):
        self.pos = 0

    def read(self, skip_empty: bool = True):
        if self.pos >= len(self.data):
            raise StopIteration
        row = self.data[self.pos]
        self.pos += 1
        return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER):
        chunk = []
        for _ in range(num):
            try:
                chunk.append(self.read())
            except StopIteration:
                break
        return chunk


class TestBaseIterable:
    """Test BaseIterable class"""

    def test_cannot_instantiate_abstract_class(self):
        """Test that BaseIterable cannot be instantiated directly (ABC)"""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseIterable()

    def test_has_totals(self):
        """Test has_totals returns False by default"""
        assert BaseIterable.has_totals() is False

    def test_has_tables(self):
        """Test has_tables returns False by default"""
        assert BaseIterable.has_tables() is False

    def test_list_tables(self):
        """Test list_tables returns None by default"""
        iterable = ConcreteIterable()
        assert iterable.list_tables() is None
        assert iterable.list_tables("test.csv") is None

    def test_is_flatonly(self):
        """Test is_flatonly returns False by default"""
        assert BaseIterable.is_flatonly() is False

    def test_is_flat_returns_false_by_default(self):
        """Test is_flat returns False when is_flatonly is False"""
        iterable = ConcreteIterable()
        assert iterable.is_flat() is False

    def test_is_flat_returns_true_when_flatonly(self):
        """Test is_flat returns True when is_flatonly is True"""

        class FlatOnlyIterable(ConcreteIterable):
            @staticmethod
            def is_flatonly():
                return True

        iterable = FlatOnlyIterable()
        assert iterable.is_flat() is True

    def test_is_streaming(self):
        """Test is_streaming returns False by default"""
        iterable = ConcreteIterable()
        assert iterable.is_streaming() is False

    def test_write_raises_write_not_supported_error(self):
        """Test that write raises WriteNotSupportedError"""
        iterable = ConcreteIterable()
        with pytest.raises(WriteNotSupportedError) as exc_info:
            iterable.write({})
        assert exc_info.value.format_id == "test"
        assert "not supported" in exc_info.value.reason.lower()

    def test_write_bulk_raises_write_not_supported_error(self):
        """Test that write_bulk raises WriteNotSupportedError"""
        iterable = ConcreteIterable()
        with pytest.raises(WriteNotSupportedError) as exc_info:
            iterable.write_bulk([{}])
        assert exc_info.value.format_id == "test"
        assert "not supported" in exc_info.value.reason.lower()

    def test_iter_protocol(self):
        """Test iterator protocol"""
        iterable = ConcreteIterable([{"a": 1}, {"b": 2}])
        # __iter__ returns self
        assert iter(iterable) == iterable

    def test_next_calls_read(self):
        """Test that __next__ calls read()"""
        iterable = ConcreteIterable([{"a": 1}, {"b": 2}])
        assert next(iterable) == {"a": 1}
        assert next(iterable) == {"b": 2}
        with pytest.raises(StopIteration):
            next(iterable)

    def test_read_with_skip_empty_parameter(self):
        """Test that read() accepts skip_empty parameter"""
        iterable = ConcreteIterable([{"a": 1}])
        # Should work with default skip_empty=True
        assert iterable.read() == {"a": 1}
        iterable.reset()
        # Should work with skip_empty=False
        assert iterable.read(skip_empty=False) == {"a": 1}

    def test_read_bulk_with_default_bulk_number(self):
        """Test that read_bulk() uses DEFAULT_BULK_NUMBER"""
        iterable = ConcreteIterable([{"a": i} for i in range(150)])
        # Should read DEFAULT_BULK_NUMBER (100) records
        chunk = iterable.read_bulk()
        assert len(chunk) == DEFAULT_BULK_NUMBER
        assert chunk[0] == {"a": 0}
        assert chunk[-1] == {"a": 99}

    def test_read_bulk_with_custom_number(self):
        """Test that read_bulk() accepts custom num parameter"""
        iterable = ConcreteIterable([{"a": i} for i in range(50)])
        chunk = iterable.read_bulk(num=10)
        assert len(chunk) == 10

    def test_init_sets_closed_flag(self):
        """Test that __init__ sets _closed flag to False"""
        iterable = ConcreteIterable()
        assert iterable._closed is False

    def test_abstract_methods_must_be_implemented(self):
        """Test that abstract methods must be implemented in subclasses"""

        class IncompleteIterable(BaseIterable):
            @staticmethod
            def id():
                return "incomplete"

        # Should raise TypeError because reset, read, read_bulk are not implemented
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteIterable()


class MockCodec(BaseCodec):
    """Mock codec for testing"""

    def __init__(self, filename=None, fileobj=None, mode="r", open_it=False, options=None):
        super().__init__(filename, fileobj, mode, open_it, options)
        self.opened = False

    @staticmethod
    def fileexts():
        return ["mock"]

    def open(self):
        if self.filename:
            mode_str = f"{self.mode}b" if self.mode in ("r", "w") else self.mode
            self._fileobj = open(self.filename, mode_str)
        self.opened = True

    def close(self):
        if self._fileobj:
            if hasattr(self._fileobj, "closed") and not self._fileobj.closed:
                self._fileobj.close()
            self._fileobj = None
        self.opened = False

    def fileobj(self):
        return self._fileobj


class ConcreteFileIterable(BaseFileIterable):
    """Concrete implementation of BaseFileIterable for testing"""

    def __init__(self, filename=None, stream=None, codec=None, **kwargs):
        super().__init__(filename=filename, stream=stream, codec=codec, **kwargs)
        self._data = []
        self._pos = 0

    @staticmethod
    def id():
        return "test_file"

    def read(self, skip_empty: bool = True):
        if self._pos >= len(self._data):
            raise StopIteration
        row = self._data[self._pos]
        self._pos += 1
        return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER):
        chunk = []
        for _ in range(num):
            try:
                chunk.append(self.read())
            except StopIteration:
                break
        return chunk

    def reset(self):
        super().reset()
        self._pos = 0


class TestBaseFileIterable:
    """Test BaseFileIterable class"""

    def test_init_with_filename(self, tmp_path):
        """Test BaseFileIterable initialization with filename"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        iterable = ConcreteFileIterable(filename=str(test_file), noopen=True)
        assert iterable.filename == str(test_file)
        assert iterable.stype == ITERABLE_TYPE_FILE
        assert iterable.fobj is None

    def test_init_with_stream(self):
        """Test BaseFileIterable initialization with stream"""
        stream = io.StringIO("test data")
        iterable = ConcreteFileIterable(stream=stream, noopen=True)
        assert iterable.stype == ITERABLE_TYPE_STREAM
        assert iterable.fobj == stream

    def test_init_with_codec(self, tmp_path):
        """Test BaseFileIterable initialization with codec"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        codec = MockCodec(filename=str(test_file), mode="r")
        iterable = ConcreteFileIterable(codec=codec, noopen=True)
        assert iterable.stype == ITERABLE_TYPE_CODEC
        assert iterable.codec == codec

    def test_init_no_source_raises_error(self):
        """Test that BaseFileIterable raises error with no source"""
        with pytest.raises(ValueError, match="requires filename, stream, or codec"):
            ConcreteFileIterable(noopen=True)

    def test_init_with_options(self, tmp_path):
        """Test BaseFileIterable initialization with options"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        options = {"custom_option": "value"}
        iterable = ConcreteFileIterable(filename=str(test_file), noopen=True, options=options)
        assert iterable.custom_option == "value"

    def test_open_file_type(self, tmp_path):
        """Test open method with file type"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        iterable = ConcreteFileIterable(filename=str(test_file), noopen=True)
        iterable.open()
        assert iterable.fobj is not None
        iterable.close()

    def test_open_file_type_binary(self, tmp_path):
        """Test open method with binary mode"""
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"test data")

        iterable = ConcreteFileIterable(filename=str(test_file), binary=True, noopen=True, mode="r")
        iterable.open()
        assert iterable.fobj is not None
        assert iterable.binary is True
        iterable.close()

    def test_open_stream_type_raises_error(self):
        """Test open raises error for stream type"""
        stream = io.StringIO("test")
        iterable = ConcreteFileIterable(stream=stream, noopen=True)
        with pytest.raises(NotImplementedError):
            iterable.open()

    def test_reset_file_type(self, tmp_path):
        """Test reset method with file type"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("line1\nline2\nline3")

        iterable = ConcreteFileIterable(filename=str(test_file), noopen=False)
        # Read first line
        first_pos = iterable.fobj.tell()
        iterable.fobj.readline()
        assert iterable.fobj.tell() > first_pos

        # Reset should seek to beginning
        iterable.reset()
        assert iterable.fobj.tell() == 0
        iterable.close()

    def test_reset_codec_type(self, tmp_path):
        """Test reset method with codec type"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        codec = MockCodec(filename=str(test_file), mode="r", open_it=True)
        iterable = ConcreteFileIterable(codec=codec, noopen=False)
        # Set datamode as class attribute
        iterable.datamode = "text"
        # Reset should close and reopen
        iterable.reset()
        assert iterable.fobj is not None
        iterable.close()

    def test_reset_codec_write_mode(self, tmp_path):
        """Test reset with codec in write mode doesn't reset"""
        test_file = tmp_path / "test.txt"

        codec = MockCodec(filename=str(test_file), mode="w", open_it=True)
        iterable = ConcreteFileIterable(codec=codec, noopen=False, mode="w")
        iterable.datamode = "text"
        # In write mode, reset should not close the file
        iterable.reset()
        iterable.close()

    def test_close_file_type(self, tmp_path):
        """Test close method with file type"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        iterable = ConcreteFileIterable(filename=str(test_file), noopen=False)
        assert iterable.fobj is not None
        fobj = iterable.fobj
        assert not fobj.closed

        iterable.close()
        assert iterable.fobj is None or fobj.closed

    def test_close_codec_type(self, tmp_path):
        """Test close method with codec type"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        codec = MockCodec(filename=str(test_file), mode="r", open_it=True)
        iterable = ConcreteFileIterable(codec=codec, noopen=False)
        iterable.datamode = "text"
        iterable.close()
        assert iterable.fobj is None

    def test_close_codec_type_no_fobj(self, tmp_path):
        """Test close with codec when fobj is None"""
        test_file = tmp_path / "test.txt"
        codec = MockCodec(filename=str(test_file), mode="r")
        iterable = ConcreteFileIterable(codec=codec, noopen=True)
        iterable.close()
        # Should close codec
        assert codec.opened is False

    def test_context_manager(self, tmp_path):
        """Test context manager protocol"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        with ConcreteFileIterable(filename=str(test_file), noopen=False) as iterable:
            assert iterable.fobj is not None
            fobj = iterable.fobj
        # File should be closed after context exit (base closes and sets fobj to None)
        assert fobj.closed

    def test_datamode_default(self, tmp_path):
        """Test that datamode defaults to 'text'"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        iterable = ConcreteFileIterable(filename=str(test_file), noopen=True)
        assert iterable.datamode == "text"

    def test_base_codec_context_manager_with_fileobj(self):
        """Test BaseCodec context manager with existing fileobj"""
        fileobj = io.BytesIO(b"test")
        codec = BaseCodec(fileobj=fileobj)
        # Should not call open() since fileobj exists
        with pytest.raises(NotImplementedError):
            # Will fail on exit when close() is called
            with codec:
                pass

    def test_base_codec_textIO_encoding(self):
        """Test textIO with different encodings"""
        fileobj = io.BytesIO(b"test data")
        codec = BaseCodec(fileobj=fileobj)
        text_wrapper = codec.textIO(encoding="latin-1")
        assert isinstance(text_wrapper, io.TextIOWrapper)
        assert text_wrapper.encoding == "latin-1"

    def test_base_file_iterable_reset_stream_type(self):
        """Test reset with stream type (should not raise error)"""
        stream = io.StringIO("test data")
        iterable = ConcreteFileIterable(stream=stream, noopen=True)
        # Reset should not raise error for stream type
        iterable.reset()
        # Stream position should be unchanged (streams don't support reset)

    def test_base_file_iterable_close_stream_type(self):
        """Test close with stream type"""
        stream = io.StringIO("test")
        iterable = ConcreteFileIterable(stream=stream, noopen=True)
        # Close should not close the stream (it's managed externally)
        iterable.close()
        # Stream should still be usable
        assert stream.read() == "test"

    def test_base_file_iterable_open_write_mode(self, tmp_path):
        """Test open with write mode"""
        # Test implementation would go here
        pass


class TestBaseFileIterableFactoryMethods:
    """Test factory methods for BaseFileIterable"""

    def test_from_file_basic(self, tmp_path):
        """Test from_file factory method"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        iterable = ConcreteFileIterable.from_file(str(test_file), noopen=True)
        assert iterable.filename == str(test_file)
        assert iterable.stype == ITERABLE_TYPE_FILE
        assert iterable.fobj is None
        assert iterable.encoding == "utf8"
        assert iterable.mode == "r"

    def test_from_file_with_options(self, tmp_path):
        """Test from_file with encoding and other options"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        iterable = ConcreteFileIterable.from_file(
            str(test_file),
            encoding="latin-1",
            mode="r",
            noopen=True,
            on_error="skip",
        )
        assert iterable.encoding == "latin-1"
        assert iterable.mode == "r"
        assert iterable._on_error == "skip"

    def test_from_stream_basic(self):
        """Test from_stream factory method"""
        stream = io.StringIO("test data")
        iterable = ConcreteFileIterable.from_stream(stream)
        assert iterable.stype == ITERABLE_TYPE_STREAM
        assert iterable.fobj == stream
        assert iterable.filename is None
        assert iterable.codec is None

    def test_from_stream_with_options(self):
        """Test from_stream with options"""
        stream = io.StringIO("test data")
        iterable = ConcreteFileIterable.from_stream(stream, encoding="utf-8", on_error="warn")
        assert iterable.encoding == "utf-8"
        assert iterable._on_error == "warn"

    def test_from_codec_basic(self, tmp_path):
        """Test from_codec factory method"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        codec = MockCodec(filename=str(test_file))
        iterable = ConcreteFileIterable.from_codec(codec, noopen=True)
        assert iterable.stype == ITERABLE_TYPE_CODEC
        assert iterable.codec == codec
        assert iterable.filename is None
        assert iterable.fobj is None  # noopen=True means fobj not opened yet

    def test_from_codec_with_options(self, tmp_path):
        """Test from_codec with options"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        codec = MockCodec(filename=str(test_file))
        iterable = ConcreteFileIterable.from_codec(codec, encoding="utf-8", on_error="skip", noopen=True)
        assert iterable.encoding == "utf-8"
        assert iterable._on_error == "skip"


class TestBaseFileIterableHelperMethods:
    """Test helper methods for BaseFileIterable initialization"""

    def test_init_source_file(self, tmp_path):
        """Test _init_source with filename"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        iterable = ConcreteFileIterable.__new__(ConcreteFileIterable)
        iterable.encoding = "utf8"
        iterable.datamode = "text"
        iterable._init_source(filename=str(test_file), noopen=True)
        assert iterable.stype == ITERABLE_TYPE_FILE
        assert iterable.filename == str(test_file)

    def test_init_source_stream(self):
        """Test _init_source with stream"""
        stream = io.StringIO("test data")
        iterable = ConcreteFileIterable.__new__(ConcreteFileIterable)
        iterable.encoding = "utf8"
        iterable.datamode = "text"
        iterable._init_source(stream=stream)
        assert iterable.stype == ITERABLE_TYPE_STREAM
        assert iterable.fobj == stream

    def test_init_source_codec(self, tmp_path):
        """Test _init_source with codec"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        codec = MockCodec(filename=str(test_file))
        iterable = ConcreteFileIterable.__new__(ConcreteFileIterable)
        iterable.encoding = "utf8"
        iterable.datamode = "text"
        iterable._init_source(codec=codec, noopen=True)
        assert iterable.stype == ITERABLE_TYPE_CODEC
        assert iterable.codec == codec

    def test_init_source_no_source(self):
        """Test _init_source raises error with no source"""
        iterable = ConcreteFileIterable.__new__(ConcreteFileIterable)
        iterable.encoding = "utf8"
        iterable.datamode = "text"
        with pytest.raises(ValueError, match="requires filename, stream, or codec"):
            iterable._init_source()

    def test_init_source_multiple_sources(self):
        """Test _init_source raises error with multiple sources"""
        stream = io.StringIO("test")
        iterable = ConcreteFileIterable.__new__(ConcreteFileIterable)
        iterable.encoding = "utf8"
        iterable.datamode = "text"
        with pytest.raises(ValueError, match="exactly one source"):
            iterable._init_source(filename="test.txt", stream=stream)

    def test_init_error_handling_default(self):
        """Test _init_error_handling with default options"""
        iterable = ConcreteFileIterable.__new__(ConcreteFileIterable)
        iterable._init_error_handling({})
        assert iterable._on_error == "raise"
        assert iterable._error_log is None
        assert iterable._error_log_file is None
        assert iterable._error_log_owned is False

    def test_init_error_handling_custom_policy(self):
        """Test _init_error_handling with custom error policy"""
        iterable = ConcreteFileIterable.__new__(ConcreteFileIterable)
        iterable._init_error_handling({"on_error": "skip"})
        assert iterable._on_error == "skip"

    def test_init_error_handling_invalid_policy(self):
        """Test _init_error_handling with invalid error policy"""
        iterable = ConcreteFileIterable.__new__(ConcreteFileIterable)
        with pytest.raises(ValueError, match="Invalid 'on_error' value"):
            iterable._init_error_handling({"on_error": "invalid"})

    def test_init_error_handling_log_file_path(self):
        """Test _init_error_handling with file path for error log"""
        iterable = ConcreteFileIterable.__new__(ConcreteFileIterable)
        iterable._init_error_handling({"error_log": "/tmp/errors.log"})
        assert iterable._error_log == "/tmp/errors.log"
        assert iterable._error_log_file is None
        assert iterable._error_log_owned is True

    def test_init_error_handling_log_file_like(self):
        """Test _init_error_handling with file-like object for error log"""
        log_file = io.StringIO()
        iterable = ConcreteFileIterable.__new__(ConcreteFileIterable)
        iterable._init_error_handling({"error_log": log_file})
        assert iterable._error_log == log_file
        assert iterable._error_log_file == log_file
        assert iterable._error_log_owned is False

    def test_init_error_handling_invalid_log_type(self):
        """Test _init_error_handling with invalid error log type"""
        iterable = ConcreteFileIterable.__new__(ConcreteFileIterable)
        with pytest.raises(ValueError, match="Invalid 'error_log' value"):
            iterable._init_error_handling({"error_log": 123})

    def test_apply_options_basic(self):
        """Test _apply_options with basic options"""
        iterable = ConcreteFileIterable.__new__(ConcreteFileIterable)
        iterable.stype = ITERABLE_TYPE_FILE
        iterable.fobj = None
        iterable._apply_options({"custom_attr": "value"})
        assert iterable.custom_attr == "value"

    def test_apply_options_protected_attribute(self):
        """Test _apply_options prevents overriding protected attributes"""
        iterable = ConcreteFileIterable.__new__(ConcreteFileIterable)
        iterable.stype = ITERABLE_TYPE_FILE
        iterable.fobj = None
        with pytest.raises(ValueError, match="Cannot override protected attribute"):
            iterable._apply_options({"stype": ITERABLE_TYPE_STREAM})

    def test_apply_options_custom_protected(self):
        """Test _apply_options with custom protected set raises when overriding protected attr"""
        iterable = ConcreteFileIterable.__new__(ConcreteFileIterable)
        iterable.custom_attr = "original"
        with pytest.raises(ValueError, match="Cannot override protected attribute"):
            iterable._apply_options({"custom_attr": "new"}, protected={"custom_attr"})
        # Original value unchanged
        assert iterable.custom_attr == "original"


class TestBaseFileIterableBackwardCompatibility:
    """Test that existing __init__ calls still work (backward compatibility)"""

    def test_init_backward_compatible_file(self, tmp_path):
        """Test that old-style __init__ with filename still works"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        iterable = ConcreteFileIterable(filename=str(test_file), noopen=True)
        assert iterable.filename == str(test_file)
        assert iterable.stype == ITERABLE_TYPE_FILE

    def test_init_backward_compatible_stream(self):
        """Test that old-style __init__ with stream still works"""
        stream = io.StringIO("test data")
        iterable = ConcreteFileIterable(stream=stream, noopen=True)
        assert iterable.stype == ITERABLE_TYPE_STREAM
        assert iterable.fobj == stream

    def test_init_backward_compatible_codec(self, tmp_path):
        """Test that old-style __init__ with codec still works"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        codec = MockCodec(filename=str(test_file))
        iterable = ConcreteFileIterable(codec=codec, noopen=True)
        assert iterable.stype == ITERABLE_TYPE_CODEC
        assert iterable.codec == codec

    def test_init_backward_compatible_options(self, tmp_path):
        """Test that old-style __init__ with options still works"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        iterable = ConcreteFileIterable(
            filename=str(test_file),
            noopen=True,
            options={"on_error": "skip", "custom": "value"},
        )
        assert iterable._on_error == "skip"
        assert iterable.custom == "value"


class TestBaseFileIterableValidation:
    """Test validation in new initialization pattern"""

    def test_init_validates_exactly_one_source(self):
        """Test that __init__ validates exactly one source is provided"""
        stream = io.StringIO("test")
        with pytest.raises(ValueError, match="exactly one source"):
            ConcreteFileIterable(filename="test.txt", stream=stream, noopen=True)

    def test_init_validates_at_least_one_source(self):
        """Test that __init__ validates at least one source is provided"""
        with pytest.raises(ValueError, match="requires filename, stream, or codec"):
            ConcreteFileIterable(noopen=True)

    def test_apply_options_protects_critical_attributes(self, tmp_path):
        """Test that _apply_options protects critical attributes"""
        iterable = ConcreteFileIterable.__new__(ConcreteFileIterable)
        iterable.stype = ITERABLE_TYPE_FILE
        iterable.fobj = None
        iterable._closed = False

        # Try to override protected attributes
        protected_attrs = ["stype", "fobj", "_on_error", "_error_log", "_error_log_file", "_error_log_owned", "_closed"]
        for attr in protected_attrs:
            with pytest.raises(ValueError, match="Cannot override protected attribute"):
                iterable._apply_options({attr: "invalid"})
        test_file = tmp_path / "test.txt"
        iterable = ConcreteFileIterable(filename=str(test_file), noopen=True, mode="w")
        iterable.open()
        assert iterable.fobj is not None
        assert iterable.fobj.mode == "w"
        iterable.close()

    def test_base_file_iterable_open_append_mode(self, tmp_path):
        """Test open with append mode"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("existing")
        iterable = ConcreteFileIterable(filename=str(test_file), noopen=True, mode="a")
        iterable.open()
        assert iterable.fobj is not None
        assert iterable.fobj.mode == "a"
        iterable.close()

    def test_base_file_iterable_codec_text_mode(self, tmp_path):
        """Test BaseFileIterable with codec in text mode"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")
        codec = MockCodec(filename=str(test_file), mode="r", open_it=True)
        iterable = ConcreteFileIterable(codec=codec, noopen=False)
        iterable.datamode = "text"
        assert iterable.fobj is not None
        assert isinstance(iterable.fobj, io.TextIOWrapper)
        iterable.close()

    def test_base_file_iterable_codec_binary_mode(self, tmp_path):
        """Test BaseFileIterable with codec in binary mode"""
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"test data")
        codec = MockCodec(filename=str(test_file), mode="rb", open_it=True)
        iterable = ConcreteFileIterable(codec=codec, noopen=False, binary=True)
        iterable.datamode = "binary"
        assert iterable.fobj is not None
        # In binary mode, should not wrap with TextIOWrapper
        assert not isinstance(iterable.fobj, io.TextIOWrapper)
        iterable.close()

    def test_base_file_iterable_reset_codec_exception_handling(self, tmp_path):
        """Test reset handles exceptions when closing codec wrapper"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        codec = MockCodec(filename=str(test_file), mode="r", open_it=True)
        iterable = ConcreteFileIterable(codec=codec, noopen=False)
        iterable.datamode = "text"
        # Close the wrapper manually to simulate an error
        if iterable.fobj:
            iterable.fobj.close()
        # Reset should handle the exception gracefully
        iterable.reset()
        iterable.close()

    def test_base_file_iterable_close_codec_exception_handling(self, tmp_path):
        """Test close handles exceptions when closing codec wrapper"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        codec = MockCodec(filename=str(test_file), mode="r", open_it=True)
        iterable = ConcreteFileIterable(codec=codec, noopen=False)
        iterable.datamode = "text"
        # Manually close to simulate already closed
        if iterable.fobj:
            iterable.fobj.close()
        # Close should handle the exception gracefully
        iterable.close()

    def test_resource_leak_file_handle_closed(self, tmp_path):
        """Test that file handles are properly closed (no resource leak)"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        iterable = ConcreteFileIterable(filename=str(test_file), noopen=False)
        assert iterable.fobj is not None
        assert not iterable.fobj.closed

        # Close should close the file handle
        iterable.close()
        assert iterable.fobj is None or iterable.fobj.closed

        # Verify file handle is actually closed by checking we can't read from it
        # (if fobj is None, that's also fine - means it was cleaned up)

    def test_resource_leak_codec_cleaned_up(self, tmp_path):
        """Test that codecs are properly cleaned up (no resource leak)"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        codec = MockCodec(filename=str(test_file), mode="r", open_it=True)
        iterable = ConcreteFileIterable(codec=codec, noopen=False)
        iterable.datamode = "text"

        assert iterable.fobj is not None
        assert codec._fileobj is not None
        assert codec.opened is True

        # Close should clean up both wrapper and codec
        iterable.close()
        assert iterable.fobj is None
        assert codec.opened is False
        assert codec._fileobj is None

    def test_resource_leak_multiple_close_safe(self, tmp_path):
        """Test that multiple close() calls are safe (idempotent)"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        iterable = ConcreteFileIterable(filename=str(test_file), noopen=False)
        assert iterable.fobj is not None

        # First close
        iterable.close()
        assert iterable.fobj is None or iterable.fobj.closed

        # Second close should not raise exception
        iterable.close()

        # Third close should also be safe
        iterable.close()

    def test_resource_leak_codec_multiple_close_safe(self, tmp_path):
        """Test that multiple close() calls on codec-based iterable are safe"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        codec = MockCodec(filename=str(test_file), mode="r", open_it=True)
        iterable = ConcreteFileIterable(codec=codec, noopen=False)
        iterable.datamode = "text"

        # First close
        iterable.close()
        assert iterable.fobj is None

        # Second close should not raise exception
        iterable.close()

        # Third close should also be safe
        iterable.close()

    def test_resource_leak_exception_during_close(self, tmp_path):
        """Test that resources are cleaned up even if exception occurs during close"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        # Create a codec that raises exception on close
        class FailingCodec(MockCodec):
            def close(self):
                raise RuntimeError("Codec close failed")

        codec = FailingCodec(filename=str(test_file), mode="r", open_it=True)
        iterable = ConcreteFileIterable(codec=codec, noopen=False)
        iterable.datamode = "text"

        # Close should suppress codec exception but still clean up wrapper
        iterable.close()
        # Wrapper should be cleaned up even if codec.close() raised exception
        assert iterable.fobj is None

    def test_resource_leak_reset_cleans_up_wrapper(self, tmp_path):
        """Test that reset() properly cleans up wrapper before recreating"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        codec = MockCodec(filename=str(test_file), mode="r", open_it=True)
        iterable = ConcreteFileIterable(codec=codec, noopen=False)
        iterable.datamode = "text"

        original_fobj = iterable.fobj
        assert original_fobj is not None

        # Reset should close old wrapper and create new one
        iterable.reset()

        # New wrapper should be different object
        assert iterable.fobj is not None
        assert iterable.fobj is not original_fobj
        # Old wrapper should be closed
        assert original_fobj.closed

        iterable.close()

    def test_resource_leak_stream_not_closed(self, tmp_path):
        """Test that stream-based iterables don't close external streams"""
        stream = io.StringIO("test data")
        iterable = ConcreteFileIterable(stream=stream, noopen=True)

        # Close should not close the stream (it's managed externally)
        iterable.close()

        # Stream should still be usable
        assert not stream.closed
        stream.seek(0)
        assert stream.read() == "test data"

    def test_context_manager_file_type_cleanup(self, tmp_path):
        """Test context manager properly cleans up file-based iterable"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        with ConcreteFileIterable(filename=str(test_file), noopen=False) as iterable:
            assert iterable.fobj is not None
            assert not iterable.fobj.closed
            # File should be readable
            content = iterable.fobj.read()
            assert content == "test data"

        # After context exit, file should be closed
        assert iterable.fobj is None or iterable.fobj.closed

    def test_context_manager_codec_type_cleanup(self, tmp_path):
        """Test context manager properly cleans up codec-based iterable"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        codec = MockCodec(filename=str(test_file), mode="r", open_it=True)
        with ConcreteFileIterable(codec=codec, noopen=False) as iterable:
            iterable.datamode = "text"
            assert iterable.fobj is not None
            assert codec.opened is True

        # After context exit, both wrapper and codec should be cleaned up
        assert iterable.fobj is None
        assert codec.opened is False
        assert codec._fileobj is None

    def test_context_manager_stream_type_no_cleanup(self, tmp_path):
        """Test context manager doesn't close external streams"""
        stream = io.StringIO("test data")

        with ConcreteFileIterable(stream=stream, noopen=True) as iterable:
            assert iterable.fobj == stream
            assert not stream.closed

        # After context exit, stream should still be open (managed externally)
        assert not stream.closed
        stream.seek(0)
        assert stream.read() == "test data"

    def test_context_manager_exception_cleanup(self, tmp_path):
        """Test context manager cleans up resources even when exception occurs"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        try:
            with ConcreteFileIterable(filename=str(test_file), noopen=False) as iterable:
                assert iterable.fobj is not None
                # Raise an exception inside context
                raise ValueError("Test exception")
        except ValueError:
            pass

        # File should still be closed despite exception
        assert iterable.fobj is None or iterable.fobj.closed

    def test_context_manager_codec_exception_cleanup(self, tmp_path):
        """Test context manager cleans up codec even when exception occurs"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        codec = MockCodec(filename=str(test_file), mode="r", open_it=True)
        try:
            with ConcreteFileIterable(codec=codec, noopen=False) as iterable:
                iterable.datamode = "text"
                assert iterable.fobj is not None
                # Raise an exception inside context
                raise RuntimeError("Test exception")
        except RuntimeError:
            pass

        # Codec should still be cleaned up despite exception
        assert iterable.fobj is None
        assert codec.opened is False

    def test_context_manager_error_log_cleanup(self, tmp_path):
        """Test context manager cleans up error log file"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")
        error_log_file = tmp_path / "error.log"

        options = {"error_log": str(error_log_file)}
        with ConcreteFileIterable(filename=str(test_file), noopen=False, options=options) as iterable:
            assert iterable._error_log_file is None  # Not opened yet
            assert iterable._error_log_owned is True

        # After context exit, error log file should be cleaned up
        # (it would be opened if errors occurred, but we're just testing cleanup)

    def test_context_manager_nested_usage(self, tmp_path):
        """Test nested context manager usage"""
        test_file1 = tmp_path / "test1.txt"
        test_file1.write_text("data1")
        test_file2 = tmp_path / "test2.txt"
        test_file2.write_text("data2")

        with ConcreteFileIterable(filename=str(test_file1), noopen=False) as iterable1:
            assert iterable1.fobj is not None
            with ConcreteFileIterable(filename=str(test_file2), noopen=False) as iterable2:
                assert iterable2.fobj is not None
                # Both should be open
                assert not iterable1.fobj.closed
                assert not iterable2.fobj.closed
            # iterable2 should be closed, iterable1 still open
            assert iterable2.fobj is None or iterable2.fobj.closed
            assert not iterable1.fobj.closed
        # Both should be closed now
        assert iterable1.fobj is None or iterable1.fobj.closed
        assert iterable2.fobj is None or iterable2.fobj.closed

    def test_context_manager_return_value(self, tmp_path):
        """Test context manager returns self"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test data")

        with ConcreteFileIterable(filename=str(test_file), noopen=False) as iterable:
            # Context manager should return self
            assert isinstance(iterable, BaseFileIterable)
            assert iterable.fobj is not None
