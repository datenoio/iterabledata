"""Iterable data processing Python library."""

__author__ = "Ivan Begtin"
__version__ = "1.0.23"
__licence__ = "MIT"

from . import ingest, validate

try:
    from .ai import doc as ai
except ImportError:  # AI extras remain optional for the core package import.
    ai = None
from .exceptions import (
    CodecCompressionError,
    CodecDecompressionError,
    CodecError,
    CodecNotSupportedError,
    FormatDetectionError,
    FormatError,
    FormatNotSupportedError,
    FormatParseError,
    IterableDataError,
    ReadError,
    ResourceError,
    ResourceLeakError,
    StreamingNotSupportedError,
    StreamNotSeekableError,
    WriteError,
    WriteNotSupportedError,
)
from .helpers.async_detect import aopen_iterable
from .helpers.detect import open_iterable
from .helpers.typed import as_dataclasses, as_pydantic
from .ops import filter, inspect, schema, stats, transform
from .types import CodecArgs, IterableArgs, Row

open_it = open_iterable

__all__ = [
    "open_iterable",
    "open_it",
    "aopen_iterable",
    "Row",
    "IterableArgs",
    "CodecArgs",
    "as_dataclasses",
    "as_pydantic",
    "ai",
    "filter",
    "inspect",
    "ingest",
    "schema",
    "stats",
    "transform",
    "validate",
    "IterableDataError",
    "FormatError",
    "FormatNotSupportedError",
    "FormatDetectionError",
    "FormatParseError",
    "CodecError",
    "CodecNotSupportedError",
    "CodecDecompressionError",
    "CodecCompressionError",
    "ReadError",
    "WriteError",
    "WriteNotSupportedError",
    "StreamingNotSupportedError",
    "ResourceError",
    "StreamNotSeekableError",
    "ResourceLeakError",
]
