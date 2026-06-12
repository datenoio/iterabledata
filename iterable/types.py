"""Type aliases and type definitions for iterabledata."""

from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar, runtime_checkable

# Type variables for generic types
T = TypeVar("T")
"""Generic type variable for general use."""

T_co = TypeVar("T_co", covariant=True)
"""Covariant type variable (used for read-only types)."""

T_contra = TypeVar("T_contra", contravariant=True)
"""Contravariant type variable (used for write-only types)."""

BufferType = TypeVar("BufferType", bound=bytes | str)
"""Type variable for file buffer types (bytes for binary, str for text)."""

DataFrameType = TypeVar("DataFrameType")
"""Type variable for DataFrame types (pandas, polars, dask, etc.)."""

# Type aliases for common data structures
Row = dict[str, Any]
"""Type alias for a data row represented as a dictionary."""

IterableArgs = dict[str, Any]
"""Type alias for iterable-specific configuration arguments."""

CodecArgs = dict[str, Any]
"""Type alias for codec-specific configuration arguments."""


@runtime_checkable
class Readable(Protocol):
    """Protocol for objects that can be read from (file-like objects with read capability)."""

    def read(self, size: int = -1) -> bytes | str:
        """Read data from the object."""
        ...

    def close(self) -> None:
        """Close the object."""
        ...


@runtime_checkable
class Writable(Protocol):
    """Protocol for objects that can be written to (file-like objects with write capability)."""

    def write(self, data: bytes | str) -> int:
        """Write data to the object."""
        ...

    def close(self) -> None:
        """Close the object."""
        ...


@runtime_checkable
class Seekable(Protocol):
    """Protocol for objects that support seeking (file-like objects with seek capability)."""

    def seek(self, offset: int, whence: int = 0) -> int:
        """Seek to a position in the object."""
        ...

    def tell(self) -> int:
        """Return current position in the object."""
        ...


@runtime_checkable
class FileLike(Readable, Writable, Seekable, Protocol):
    """Protocol for complete file-like objects that support read, write, and seek operations.

    This is a combination of Readable, Writable, and Seekable protocols.
    Not all file-like objects need to implement all methods, but this protocol
    represents the full interface.
    """

    def close(self) -> None:
        """Close the file-like object."""
        ...

    def __enter__(self) -> "FileLike":
        """Context manager entry."""
        ...

    def __exit__(self, exc_type: type[Exception] | None, exc_val: Exception | None, exc_tb: Any) -> bool:
        """Context manager exit."""
        ...


@runtime_checkable
class ErrorLogWriter(Protocol):
    """Protocol for error log file-like objects that only need write capability."""

    def write(self, data: str) -> int:
        """Write error log entry."""
        ...

    def flush(self) -> None:
        """Flush buffered data."""
        ...

    def close(self) -> None:
        """Close the error log writer (optional, for file-like objects)."""
        ...


@dataclass
class ConversionResult:
    """Result object containing metrics from a conversion operation."""

    rows_in: int
    """Total number of rows read from the source file."""

    rows_out: int
    """Total number of rows written to the destination file."""

    elapsed_seconds: float
    """Total elapsed time in seconds for the conversion."""

    bytes_read: int | None = None
    """Number of bytes read from source (if available)."""

    bytes_written: int | None = None
    """Number of bytes written to destination (if available)."""

    errors: list[Exception] = field(default_factory=list)
    """List of errors encountered during conversion (empty if none)."""


@dataclass
class FileConversionResult:
    """Result object for a single file conversion within a bulk operation."""

    source_file: str
    """Path to the source file that was converted."""

    dest_file: str
    """Path to the destination file that was created."""

    result: ConversionResult | None
    """ConversionResult from the individual file conversion, or None if conversion failed."""

    error: Exception | None = None
    """Exception raised during conversion, or None if conversion succeeded."""

    @property
    def success(self) -> bool:
        """Whether the conversion succeeded."""
        return self.error is None and self.result is not None


@dataclass
class BulkConversionResult:
    """Result object containing aggregated metrics from a bulk conversion operation."""

    total_files: int
    """Total number of files processed."""

    successful_files: int
    """Number of files successfully converted."""

    failed_files: int
    """Number of files that failed to convert."""

    total_rows_in: int
    """Total number of rows read across all files."""

    total_rows_out: int
    """Total number of rows written across all files."""

    total_elapsed_seconds: float
    """Total elapsed time in seconds for all conversions."""

    file_results: list[FileConversionResult] = field(default_factory=list)
    """List of results for each individual file conversion."""

    errors: list[Exception] = field(default_factory=list)
    """List of all errors encountered during bulk conversion."""

    @property
    def throughput(self) -> float | None:
        """Calculate rows per second throughput."""
        if self.total_elapsed_seconds > 0:
            return self.total_rows_out / self.total_elapsed_seconds
        return None


class PipelineResult:
    """Result object containing metrics from a pipeline execution.

    Supports both attribute access (result.rows_processed) and dictionary access
    (result["rec_count"]) for backward compatibility.
    """

    def __init__(
        self,
        rows_processed: int,
        elapsed_seconds: float,
        exceptions: int,
        nulls: int = 0,
        rec_count: int | None = None,
        time_start: float | None = None,
        time_end: float | None = None,
        duration: float | None = None,
    ):
        self.rows_processed = rows_processed
        self.elapsed_seconds = elapsed_seconds
        self.exceptions = exceptions
        self.nulls = nulls
        self.rec_count = rec_count if rec_count is not None else rows_processed
        self.time_start = time_start
        self.time_end = time_end
        self.duration = duration if duration is not None else elapsed_seconds

    @property
    def throughput(self) -> float | None:
        """Calculate rows per second throughput."""
        if self.elapsed_seconds > 0:
            return self.rows_processed / self.elapsed_seconds
        return None

    def __getitem__(self, key: str) -> Any:
        """Support dictionary-style access for backward compatibility."""
        if key == "rec_count":
            return self.rec_count
        elif key == "rows_processed":
            return self.rows_processed
        elif key == "nulls":
            return self.nulls
        elif key == "exceptions":
            return self.exceptions
        elif key == "time_start":
            return self.time_start
        elif key == "time_end":
            return self.time_end
        elif key == "duration":
            return self.duration
        elif key == "elapsed_seconds":
            return self.elapsed_seconds
        elif key == "throughput":
            return self.throughput
        else:
            raise KeyError(f"Key '{key}' not found in PipelineResult")

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator for backward compatibility."""
        return key in {
            "rec_count",
            "rows_processed",
            "nulls",
            "exceptions",
            "time_start",
            "time_end",
            "duration",
            "elapsed_seconds",
            "throughput",
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Support dict.get() method for backward compatibility."""
        try:
            return self[key]
        except KeyError:
            return default

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return {
            "rec_count": self.rec_count,
            "rows_processed": self.rows_processed,
            "nulls": self.nulls,
            "exceptions": self.exceptions,
            "time_start": self.time_start,
            "time_end": self.time_end,
            "duration": self.duration,
            "elapsed_seconds": self.elapsed_seconds,
            "throughput": self.throughput,
        }
