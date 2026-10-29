"""Iterable data processing Python library."""

__author__ = "Ivan Begtin"
__version__ = "1.1.0"
__licence__ = "MIT"

from . import ingest, validate
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


def __getattr__(name: str) -> object:
    """Import ``iterable.ai`` on first access.

    The AI stack pulls in HTTP clients and provider SDKs, so the package root does not
    import it eagerly. ``iterable.ai`` is the ``iterable.ai`` package (``iterable.ai.generate``
    and ``iterable.ai.doc`` are re-exported there), or ``None`` when the AI extras are missing.
    """
    if name == "ai":
        import importlib

        try:
            module: object = importlib.import_module(".ai", __name__)
        except ImportError:  # AI extras remain optional for the core package import.
            module = None
        globals()["ai"] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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
