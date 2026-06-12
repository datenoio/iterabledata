import io
import json
import typing
import warnings
from abc import ABC, abstractmethod
from datetime import datetime
from types import TracebackType
from typing import TYPE_CHECKING, Any

from .exceptions import ReadError, WriteNotSupportedError
from .helpers.debug import file_io_logger, is_debug_enabled
from .helpers.read_ahead import ReadAheadBuffer
from .helpers.validation import ValidationHook, apply_validation_hooks
from .types import ErrorLogWriter, Row

if TYPE_CHECKING:
    pass

ITERABLE_TYPE_STREAM = 10
ITERABLE_TYPE_FILE = 20
ITERABLE_TYPE_CODEC = 30
DEFAULT_BULK_NUMBER = 100


class BaseCodec:
    """Basic codec class"""

    def __init__(
        self,
        filename: str | None = None,
        fileobj: typing.IO[Any] | None = None,
        mode: str = "r",
        open_it: bool = False,
        options: dict[str, Any] | None = None,
    ) -> None:
        if options is None:
            options = {}
        self._fileobj: typing.IO[Any] | None = fileobj
        self.filename = filename
        self.mode = mode
        if open_it:
            self.open()

        if len(options) > 0:
            for k, v in options.items():
                setattr(self, k, v)
        pass

    @staticmethod
    def fileexts() -> list[str]:
        """Return file extensions"""
        raise NotImplementedError

    def reset(self) -> None:
        """Reset file"""
        #        if self._fileobj.seekable():
        #            self._fileobj.seek(0)
        #        else:
        self.close()
        self.open()

    def open(self) -> None:
        """Open codec file object"""
        raise NotImplementedError

    def fileobj(self) -> typing.IO[Any]:
        """Return file object"""
        if self._fileobj is None:
            raise ValueError("File object is not initialized")
        return self._fileobj

    def close(self) -> None:
        """Close codec. Not implemented by default"""
        raise NotImplementedError

    def __enter__(self) -> "BaseCodec":
        """Context manager entry"""
        if self._fileobj is None and self.filename is not None:
            self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit"""
        self.close()

    def textIO(self, encoding: str = "utf8") -> io.TextIOWrapper:
        """Return text wrapper over binary stream"""
        return io.TextIOWrapper(self.fileobj(), encoding=encoding, write_through=False)


class BaseIterable(ABC):
    """Base iterable data class"""

    def __init__(self):
        """Initialize base iterable"""
        self._closed = False
        self._validation_hooks: list[ValidationHook] = []
        self._on_validation_error: str = "raise"

    def _apply_validation_hooks(self, row: Row) -> Row | None:
        """
        Apply validation hooks to a row.

        Args:
            row: Row to validate

        Returns:
            Validated row, or None if skipped (when on_validation_error='skip')
        """
        return apply_validation_hooks(row, self._validation_hooks, self._on_validation_error)

    @abstractmethod
    def reset(self) -> None:
        """Reset iterator"""
        pass

    @staticmethod
    @abstractmethod
    def id() -> str:
        """Identifier of selected destination"""
        pass

    @staticmethod
    def has_totals() -> bool:
        """Has totals. Default: False"""
        return False

    @staticmethod
    def has_tables() -> bool:
        """Indicates if this format supports multiple tables/sheets/datasets.

        Returns:
            bool: True if format supports table listing, False otherwise.
        """
        return False

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List available tables, sheets, datasets, or other named collections.

        Can be called as:
        - Instance method: `iterable.list_tables()` - uses already opened file
        - Class method: `XLSXIterable.list_tables(filename)` - opens file temporarily

        Args:
            filename: Optional filename for class method usage. If None, uses instance's filename.

        Returns:
            list[str] | None: List of table/sheet names, or None if not supported.
            Returns empty list [] if file has no tables.
        """
        return None

    @abstractmethod
    def read(self, skip_empty: bool = True) -> Row:
        """Read single record"""
        pass

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[Row]:
        """Read multiple records.

        Default implementation calls read() repeatedly until num records are
        collected or the source is exhausted. Subclasses may override this
        with a format-specific optimized implementation (e.g. batch readers).

        When no more records are available, returns an empty list [] and
        does NOT raise StopIteration.
        """
        chunk: list[Row] = []
        for _ in range(num):
            try:
                chunk.append(self.read())
            except StopIteration:
                break
        return chunk

    @staticmethod
    def is_flatonly() -> bool:
        """Is source flat by only. Default: False"""
        return False

    def is_flat(self) -> bool:
        """Is source flat. Default: False"""
        if self.__class__().is_flatonly():
            return True
        # For non-flat-only formats, default to False
        return False

    def is_streaming(self) -> bool:
        """Is source streaming. Default: False"""
        return False

    def __next__(self) -> Row:
        return self.read()

    def __iter__(self) -> typing.Iterator[Row]:
        #        self.reset()
        return self

    def write(self, record: Row) -> None:
        """Write single record.

        Default implementation raises WriteNotSupportedError.
        Subclasses that support writing should override this method.
        Validation hooks are applied before writing if configured.
        """
        # Apply validation hooks before writing
        if self._validation_hooks:
            validated = self._apply_validation_hooks(record)
            if validated is None:  # Skipped
                return  # Don't write invalid row
            record = validated

        raise WriteNotSupportedError(
            format_id=self.id(),
            reason="Write operation not supported for this format",
        )

    def write_bulk(self, records: list[Row]) -> None:
        """Write multiple records.

        Default implementation raises WriteNotSupportedError.
        Subclasses that support writing should override this method.
        Validation hooks are applied before writing if configured.
        """
        # Apply validation hooks before writing
        if self._validation_hooks:
            validated_records = []
            for record in records:
                validated = self._apply_validation_hooks(record)
                if validated is not None:  # Not skipped
                    validated_records.append(validated)
            records = validated_records

        raise WriteNotSupportedError(
            format_id=self.id(),
            reason="Write operation not supported for this format",
        )

    def to_pandas(self, chunksize: int | None = None) -> Any:
        """Convert iterable to pandas DataFrame(s).

        Args:
            chunksize: If None, return a single DataFrame with all data.
                       If specified, return an iterator of DataFrames with at most
                       chunksize rows each (except possibly the last chunk).

        Returns:
            If chunksize is None: pandas DataFrame
            If chunksize is specified: Iterator of pandas DataFrames

        Raises:
            ImportError: If pandas is not installed. Message includes installation instructions.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_pandas(). Install it with: pip install pandas") from None

        if chunksize is None:
            # Collect all rows and return single DataFrame
            rows = list(self)
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame(rows)
        else:
            # Return iterator of DataFrames
            def _chunked_iterator():
                chunk = []
                for row in self:
                    chunk.append(row)
                    if len(chunk) >= chunksize:
                        yield pd.DataFrame(chunk)
                        chunk = []
                if chunk:
                    yield pd.DataFrame(chunk)

            return _chunked_iterator()

    def to_polars(self, chunksize: int | None = None) -> Any:
        """Convert iterable to Polars DataFrame(s).

        Args:
            chunksize: If None, return a single DataFrame with all data.
                       If specified, return an iterator of DataFrames with at most
                       chunksize rows each (except possibly the last chunk).

        Returns:
            If chunksize is None: polars DataFrame
            If chunksize is specified: Iterator of polars DataFrames

        Raises:
            ImportError: If polars is not installed. Message includes installation instructions.
        """
        try:
            import polars as pl
        except ImportError:
            raise ImportError("polars is required for to_polars(). Install it with: pip install polars") from None

        if chunksize is None:
            # Collect all rows and return single DataFrame
            rows = list(self)
            if not rows:
                return pl.DataFrame()
            return pl.DataFrame(rows)
        else:
            # Return iterator of DataFrames
            def _chunked_iterator():
                chunk = []
                for row in self:
                    chunk.append(row)
                    if len(chunk) >= chunksize:
                        yield pl.DataFrame(chunk)
                        chunk = []
                if chunk:
                    yield pl.DataFrame(chunk)

            return _chunked_iterator()

    def to_dask(self, chunksize: int = 1000000) -> Any:
        """Convert iterable to Dask DataFrame.

        Args:
            chunksize: Number of rows per partition. Default: 1000000.

        Returns:
            Dask DataFrame representing the iterable data.

        Raises:
            ImportError: If dask or pandas is not installed. Message includes installation instructions.
        """
        try:
            import dask.dataframe as dd
            import pandas as pd
        except ImportError as e:
            if "dask" in str(e).lower():
                raise ImportError(
                    "dask[dataframe] is required for to_dask(). Install it with: pip install 'dask[dataframe]'"
                ) from None
            else:
                raise ImportError("pandas is required for to_dask(). Install it with: pip install pandas") from None

        # Collect all rows first (Dask needs to know the structure)
        rows = list(self)
        if not rows:
            # Return empty Dask DataFrame
            return dd.from_pandas(pd.DataFrame(), npartitions=1)

        # Convert to pandas first, then to Dask
        df = pd.DataFrame(rows)
        return dd.from_pandas(df, npartitions=max(1, len(df) // chunksize))


class BaseFileIterable(BaseIterable):
    """Basic file iterable"""

    datamode = "text"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        binary: bool = False,
        encoding: str = "utf8",
        noopen: bool = False,
        mode: str = "r",
        options: dict[str, Any] | None = None,
    ) -> None:
        """Initialize BaseFileIterable.

        This method is maintained for backward compatibility. For new code,
        consider using factory methods:
        - BaseFileIterable.from_file() for file-based access
        - BaseFileIterable.from_stream() for stream-based access
        - BaseFileIterable.from_codec() for codec-based access

        Args:
            filename: Path to file (mutually exclusive with stream/codec)
            stream: Open file-like object (mutually exclusive with filename/codec)
            codec: Codec instance (mutually exclusive with filename/stream)
            binary: Whether to use binary mode
            encoding: Text encoding (default: 'utf8')
            noopen: If True, don't open the source immediately
            mode: File mode ('r', 'w', 'rb', 'wb')
            options: Additional options dictionary

        Raises:
            ValueError: If multiple sources provided or no source provided
        """
        super().__init__()  # Initialize BaseIterable (_closed flag)

        if options is None:
            options = {}

        # Set basic attributes
        self.filename = filename
        self.noopen = noopen
        self.encoding = encoding
        self.binary = binary
        self.mode = mode
        self.codec = codec
        self.fobj = None
        if self.binary:
            self.datamode = "binary"

        # Initialize source (validates and sets up file object)
        self._init_source(filename, stream, codec, noopen)

        # Initialize error handling
        self._init_error_handling(options)

        # Initialize validation hooks (extract before _apply_options)
        validation_hook = options.pop("validation_hook", None)
        if validation_hook is not None:
            if isinstance(validation_hook, list):
                self._validation_hooks = list(validation_hook)
            else:
                self._validation_hooks = [validation_hook]
        else:
            self._validation_hooks = []
        self._on_validation_error = options.pop("on_validation_error", "raise")

        # Apply additional options (with protection)
        self._apply_options(options)

        # Store debug flag from options
        self._debug = options.get("_debug", False) or is_debug_enabled()

        # Read-ahead configuration
        self._read_ahead_enabled = options.get("read_ahead", False)
        self._read_ahead_size = options.get("read_ahead_size", 10)
        self._read_ahead_refill_threshold = options.get("read_ahead_refill_threshold", 0.3)
        self._read_ahead_buffer: ReadAheadBuffer | None = None

    def _init_source(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        noopen: bool = False,
    ) -> None:
        """Initialize the data source (file, stream, or codec).

        Validates that exactly one source is provided and sets up the file object.

        Args:
            filename: Path to file
            stream: Open file-like object
            codec: Codec instance
            noopen: If True, don't open the source immediately

        Raises:
            ValueError: If no source or multiple sources provided
        """
        # Count provided sources
        sources = [filename, stream, codec]
        provided = [s for s in sources if s is not None]

        if len(provided) == 0:
            raise ValueError("BaseFileIterable requires filename, stream, or codec")
        if len(provided) > 1:
            source_types = []
            if filename is not None:
                source_types.append("filename")
            if stream is not None:
                source_types.append("stream")
            if codec is not None:
                source_types.append("codec")
            raise ValueError(f"BaseFileIterable requires exactly one source. Provided: {', '.join(source_types)}")

        # Determine source type and initialize
        if stream is not None:
            self.stype = ITERABLE_TYPE_STREAM
            self.fobj = stream
        elif filename is not None:
            self.stype = ITERABLE_TYPE_FILE
            self.filename = filename
            if not noopen:
                self.open()
        elif codec is not None:
            self.stype = ITERABLE_TYPE_CODEC
            self.codec = codec
            if not noopen:
                self.codec.open()
                self.fobj = self.codec.fileobj()
                if self.datamode == "text":
                    self.fobj = self.codec.textIO(encoding=self.encoding)

    def _init_error_handling(self, options: dict[str, Any]) -> None:
        """Initialize error handling configuration.

        Separates error handling setup from source initialization.

        Args:
            options: Options dictionary containing error handling settings
        """
        self._on_error = options.get("on_error", "raise")
        self._error_log = options.get("error_log", None)
        self._error_log_file = None
        self._error_log_owned = False

        # Validate error policy
        if self._on_error not in ("raise", "skip", "warn"):
            raise ValueError(f"Invalid 'on_error' value: '{self._on_error}'. Valid values are: 'raise', 'skip', 'warn'")

        # Setup error logging
        if self._error_log is not None:
            if isinstance(self._error_log, str):
                # File path - we'll open it when needed
                self._error_log_file = None
                self._error_log_owned = True
            elif isinstance(self._error_log, ErrorLogWriter):
                # File-like object that implements ErrorLogWriter protocol
                self._error_log_file = self._error_log
                self._error_log_owned = False
            else:
                raise ValueError(
                    f"Invalid 'error_log' value: must be file path (str) or "
                    f"file-like object with write() method, "
                    f"got {type(self._error_log).__name__}"
                )

    def _apply_options(self, options: dict[str, Any], protected: set[str] | None = None) -> None:
        """Apply options dictionary with validation.

        Prevents options from overriding critical attributes.

        Args:
            options: Dictionary of options to apply
            protected: Set of attribute names that cannot be overridden.
                      If None, uses default protected set.

        Raises:
            ValueError: If attempting to override a protected attribute
        """
        if protected is None:
            protected = {"stype", "fobj", "_on_error", "_error_log", "_error_log_file", "_error_log_owned", "_closed"}

        for key, value in options.items():
            if key in protected:
                raise ValueError(
                    f"Cannot override protected attribute '{key}' via options. "
                    f"Use the appropriate parameter or factory method instead."
                )
            setattr(self, key, value)

    @classmethod
    def from_file(
        cls,
        filename: str,
        mode: str = "r",
        encoding: str = "utf8",
        binary: bool = False,
        noopen: bool = False,
        **options: Any,
    ) -> "BaseFileIterable":
        """Create BaseFileIterable from a file path.

        Args:
            filename: Path to the file
            mode: File mode ('r', 'w', 'rb', 'wb')
            encoding: Text encoding (default: 'utf8')
            binary: Whether to open in binary mode
            noopen: If True, don't open the file immediately
            **options: Additional options (on_error, error_log, etc.)

        Returns:
            BaseFileIterable instance configured for file-based access

        Example:
            >>> iterable = BaseFileIterable.from_file("data.csv", encoding="utf-8")
        """
        return cls(
            filename=filename,
            stream=None,
            codec=None,
            binary=binary,
            encoding=encoding,
            noopen=noopen,
            mode=mode,
            options=options,
        )

    @classmethod
    def from_stream(
        cls,
        stream: typing.IO[Any],
        encoding: str = "utf8",
        binary: bool = False,
        **options: Any,
    ) -> "BaseFileIterable":
        """Create BaseFileIterable from an open stream.

        Args:
            stream: Open file-like object (already opened)
            encoding: Text encoding (default: 'utf8')
            binary: Whether stream is binary
            **options: Additional options (on_error, error_log, etc.)

        Returns:
            BaseFileIterable instance configured for stream-based access

        Example:
            >>> with open("data.csv") as f:
            ...     iterable = BaseFileIterable.from_stream(f)
        """
        return cls(
            filename=None,
            stream=stream,
            codec=None,
            binary=binary,
            encoding=encoding,
            noopen=False,  # Stream is already open
            mode="r",  # Not applicable for streams
            options=options,
        )

    @classmethod
    def from_codec(
        cls,
        codec: BaseCodec,
        encoding: str = "utf8",
        noopen: bool = False,
        **options: Any,
    ) -> "BaseFileIterable":
        """Create BaseFileIterable from a codec.

        Args:
            codec: Codec instance (e.g., GZIPCodec, BZIP2Codec)
            encoding: Text encoding (default: 'utf8')
            noopen: If True, don't open the codec immediately
            **options: Additional options (on_error, error_log, etc.)

        Returns:
            BaseFileIterable instance configured for codec-based access

        Example:
            >>> from iterable.codecs.gzipcodec import GZIPCodec
            >>> codec = GZIPCodec(filename="data.csv.gz")
            >>> iterable = BaseFileIterable.from_codec(codec)
        """
        return cls(
            filename=None,
            stream=None,
            codec=codec,
            binary=False,  # Codec handles binary/text
            encoding=encoding,
            noopen=noopen,
            mode="r",  # Codec handles mode
            options=options,
        )

    def open(self) -> typing.IO[Any] | None:
        """Open file as file data source"""
        if self.stype == ITERABLE_TYPE_FILE:
            if self.filename is None:
                raise ValueError("Cannot open file: filename is None")
            filename: str = self.filename  # Type narrowing for mypy

            if getattr(self, "_debug", False):
                file_io_logger.debug(
                    f"Opening file: {filename} (mode: {self.mode}, binary: {self.binary}, encoding: {self.encoding})"
                )

            try:
                self.fobj = (
                    open(filename, self.mode + "b")
                    if self.binary
                    else open(filename, self.mode, encoding=self.encoding)
                )
                if getattr(self, "_debug", False):
                    file_io_logger.debug(f"File opened successfully: {filename}")
                return self.fobj
            except Exception as e:
                if getattr(self, "_debug", False):
                    file_io_logger.error(f"Failed to open file {filename}: {e}", exc_info=True)
                raise
        else:
            raise NotImplementedError

    def reset(self) -> None:
        """Reset file using seek(0).

        For file-based sources, seeks to the beginning of the file.
        For codec-based sources, resets the codec and recreates the file object.
        For stream-based sources, raises ReadError if the stream is not seekable.

        Raises:
            ReadError: If attempting to reset a non-seekable stream.
        """
        if getattr(self, "_debug", False):
            file_io_logger.debug(f"Resetting file: {getattr(self, 'filename', 'stream/codec')}")

        if self.stype == ITERABLE_TYPE_FILE:
            if self.fobj is not None:
                # Check if file object is seekable before attempting to seek
                if hasattr(self.fobj, "seekable") and not self.fobj.seekable():
                    raise ReadError(
                        f"Cannot reset: file '{self.filename}' is not seekable (e.g., stdin, network stream)",
                        filename=self.filename,
                        error_code="STREAM_NOT_SEEKABLE",
                    )
                try:
                    self.fobj.seek(0)
                except (OSError, AttributeError) as e:
                    raise ReadError(
                        f"Cannot reset: failed to seek to beginning of file '{self.filename}': {str(e)}",
                        filename=self.filename,
                        error_code="SEEK_FAILED",
                    ) from e
        elif self.stype == ITERABLE_TYPE_STREAM:
            if self.fobj is not None:
                # Check if stream is seekable
                if hasattr(self.fobj, "seekable") and not self.fobj.seekable():
                    raise ReadError(
                        "Cannot reset: stream is not seekable (e.g., stdin, network stream)",
                        filename=getattr(self, "filename", None),
                        error_code="STREAM_NOT_SEEKABLE",
                    )
                try:
                    self.fobj.seek(0)
                except (OSError, AttributeError) as e:
                    raise ReadError(
                        f"Cannot reset: failed to seek to beginning of stream: {str(e)}",
                        filename=getattr(self, "filename", None),
                        error_code="SEEK_FAILED",
                    ) from e
        elif self.stype == ITERABLE_TYPE_CODEC:
            if self.fobj is not None and self.mode not in ["w", "wb"]:
                # Close any existing wrapper to avoid leaks and ensure buffers are flushed.
                # Only suppress expected exceptions (already closed, etc.)
                try:
                    self.fobj.close()
                except (OSError, ValueError, AttributeError):
                    # These are expected when file is already closed or invalid
                    # Log but don't fail - we're about to recreate the fileobj anyway
                    pass
                except Exception as e:
                    # Unexpected exceptions should be raised
                    raise ReadError(
                        f"Cannot reset: unexpected error closing codec wrapper: {str(e)}",
                        filename=self.filename,
                        error_code="RESET_FAILED",
                    ) from e
                if self.codec is not None:
                    try:
                        self.codec.reset()
                        self.fobj = self.codec.fileobj()
                        if self.datamode == "text":
                            self.fobj = self.codec.textIO(encoding=self.encoding)
                    except Exception as e:
                        raise ReadError(
                            f"Cannot reset: failed to reset codec: {str(e)}",
                            filename=self.filename,
                            error_code="CODEC_RESET_FAILED",
                        ) from e

        # Clear read-ahead buffer if it exists
        if self._read_ahead_buffer is not None:
            self._read_ahead_buffer.clear()
            self._read_ahead_buffer = None

    def close(self) -> None:
        """Close file as file data source.

        Ensures proper cleanup of file objects and codecs:
        - For file-based sources: closes the file object
        - For codec-based sources: closes the wrapper (to flush buffers) then the codec
        - For stream-based sources: no cleanup (streams are managed externally)
        """
        if self.stype == ITERABLE_TYPE_FILE:
            if self.fobj is not None:
                self.fobj.close()
                self.fobj = None
        elif self.stype == ITERABLE_TYPE_CODEC:
            # Close wrapper first to flush any buffered text, which is critical for codecs.
            # Use try/finally to ensure fobj is set to None even if close() fails
            if self.fobj is not None:
                try:
                    self.fobj.close()
                except (OSError, ValueError, AttributeError):
                    # Expected exceptions when already closed or invalid
                    pass
                finally:
                    self.fobj = None
            # Always close the codec to ensure proper cleanup (e.g., compression finalization)
            if self.codec is not None:
                try:
                    self.codec.close()
                except Exception:
                    # Suppress exceptions during cleanup to ensure we don't mask original errors
                    pass

    def __iter__(self) -> typing.Iterator[Row]:
        """Iterator with optional read-ahead caching and validation hooks.

        If read-ahead is enabled, returns a ReadAheadBuffer that prefetches
        rows from the source iterator. Otherwise, returns self for standard
        iteration. Validation hooks are applied to each row during iteration.
        """
        if self._read_ahead_enabled:
            # Create an iterator that calls read() until StopIteration
            def base_iterator():
                while True:
                    try:
                        row = self.read()
                        # Apply validation hooks
                        if self._validation_hooks:
                            validated = self._apply_validation_hooks(row)
                            if validated is None:  # Skipped
                                continue  # Try next row
                            yield validated
                        else:
                            yield row
                    except StopIteration:
                        break

            # Wrap with read-ahead buffer
            self._read_ahead_buffer = ReadAheadBuffer(
                base_iterator(),
                buffer_size=self._read_ahead_size,
                refill_threshold=self._read_ahead_refill_threshold,
            )
            return iter(self._read_ahead_buffer)
        else:
            # Standard iteration with validation hooks
            if self._validation_hooks:

                def validated_iterator():
                    while True:
                        try:
                            row = self.read()
                            validated = self._apply_validation_hooks(row)
                            if validated is None:  # Skipped
                                continue  # Try next row
                            yield validated
                        except StopIteration:
                            break

                return validated_iterator()
            else:
                return super().__iter__()

    def __enter__(self) -> "BaseFileIterable":
        """Context manager entry"""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit"""
        self.close()
        # Close error log file if we own it
        if self._error_log_owned and self._error_log_file is not None:
            try:
                self._error_log_file.close()
            except Exception:
                pass
            self._error_log_file = None

    def _handle_error(
        self,
        error: Exception,
        row_number: int | None = None,
        byte_offset: int | None = None,
        original_line: str | None = None,
    ) -> None:
        """Handle error according to configured error policy.

        Args:
            error: The exception that occurred
            row_number: Optional row number where error occurred
            byte_offset: Optional byte offset where error occurred
            original_line: Optional original line content that failed

        Raises:
            The original error if policy is 'raise', otherwise returns None
        """
        from .exceptions import FormatParseError, ReadError

        # Enhance error with contextual information if it's a parse/read error
        if isinstance(error, (FormatParseError, ReadError)):
            if not hasattr(error, "filename") or error.filename is None:
                error.filename = getattr(self, "filename", None)
            if not hasattr(error, "row_number") or error.row_number is None:
                error.row_number = row_number
            if not hasattr(error, "byte_offset") or error.byte_offset is None:
                error.byte_offset = byte_offset
            if not hasattr(error, "original_line") or error.original_line is None:
                error.original_line = original_line

        # Log error if logging is enabled
        if self._error_log is not None:
            self._log_error(error, row_number, byte_offset, original_line)

        # Apply error policy
        if self._on_error == "raise":
            raise error
        elif self._on_error == "warn":
            # Build warning message with context
            warning_msg = "Parse error"
            if hasattr(error, "filename") and error.filename:
                warning_msg += f" in {error.filename}"
            if row_number is not None:
                warning_msg += f" at row {row_number}"
            if byte_offset is not None:
                warning_msg += f" (byte {byte_offset})"
            warning_msg += f": {str(error)}"
            warnings.warn(warning_msg, UserWarning, stacklevel=3)
        # For 'skip', just return None (error is logged but not raised)

    def _log_error(
        self,
        error: Exception,
        row_number: int | None = None,
        byte_offset: int | None = None,
        original_line: str | None = None,
    ) -> None:
        """Log error to error log file.

        Args:
            error: The exception that occurred
            row_number: Optional row number where error occurred
            byte_offset: Optional byte offset where error occurred
            original_line: Optional original line content that failed
        """
        # Open error log file if needed (for file path strings)
        if self._error_log_owned and self._error_log_file is None:
            try:
                if isinstance(self._error_log, str):
                    self._error_log_file = open(self._error_log, "a", encoding="utf-8")
            except Exception:
                # If we can't open the log file, silently fail
                return

        if self._error_log_file is None:
            return

        # Build log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "filename": getattr(self, "filename", None),
            "row_number": row_number,
            "byte_offset": byte_offset,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "original_line": original_line[:1000] if original_line else None,  # Truncate very long lines
        }

        # Write as JSON line
        try:
            self._error_log_file.write(json.dumps(log_entry) + "\n")
            self._error_log_file.flush()
        except Exception:
            # If logging fails, silently continue
            pass
