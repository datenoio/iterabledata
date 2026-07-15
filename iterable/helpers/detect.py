from __future__ import annotations

import importlib
from typing import IO, Any, TypedDict, cast

import chardet

from ..base import BaseCodec, BaseIterable

# Database driver registry helpers — re-exported for tests patching
# ``iterable.helpers.detect.get_driver`` / ``is_database_engine``.
from ..db import get_driver, is_database_engine  # noqa: F401

# Re-exported driver classes for patching as ``iterable.helpers.detect.<Driver>``.
from ..db.clickhouse import ClickHouseDriver  # noqa: F401
from ..db.postgres import PostgresDriver  # noqa: F401
from .content_detection import detect_file_type_from_content
from .debug import format_detection_logger, is_debug_enabled
from .format_registry import (
    build_datatype_registry,
    build_flat_types,
    build_read_only_formats,
    build_text_data_types,
    install_extra_hint,
)


def _load_symbol(module_path: str, symbol: str) -> Any:
    """
    Lazy-load a datatype/codec class to avoid importing all optional dependencies at import time.
    """
    try:
        module = importlib.import_module(module_path)
        return getattr(module, symbol)
    except ImportError as e:
        extra = install_extra_hint(module_path)
        if extra:
            install_msg = f"Install it with: pip install 'iterabledata[{extra}]'"
        else:
            install_msg = (
                "Install the matching optional extra (see "
                "'[project.optional-dependencies]' in pyproject.toml), or "
                "pip install 'iterabledata[all]'"
            )
        raise ImportError(
            f"Failed to import '{symbol}' from '{module_path}': {e}. "
            f"This format/codec requires an optional dependency that is not installed. "
            f"{install_msg}"
        ) from e


# Plugin discovery flag
_plugins_discovered = False


def _ensure_plugins_discovered() -> None:
    """Ensure plugins are discovered (lazy discovery)."""
    global _plugins_discovered
    if not _plugins_discovered:
        try:
            from ..plugins import discover_plugins

            discover_plugins()
        except Exception as e:
            # Don't let a broken plugin block built-in formats, but surface the
            # failure at warning level so misconfigured entry points are visible.
            format_detection_logger.warning("Plugin discovery failed: %s", e)
        _plugins_discovered = True


def _get_format_registry() -> dict[str, tuple[str, str]]:
    """Get merged format registry (built-in + plugins).

    Built-in formats take precedence over plugins.
    """
    _ensure_plugins_discovered()

    # Start with built-in formats (take precedence)
    merged = DATATYPE_REGISTRY.copy()

    # Add plugin formats (don't override built-in)
    try:
        from ..plugins import get_plugin_registry

        registry = get_plugin_registry()
        for format_id, value in registry._formats.items():
            if format_id not in merged:
                merged[format_id] = value
    except Exception as e:
        format_detection_logger.warning("Failed to load plugin formats: %s", e)

    return merged


def _get_codec_registry() -> dict[str, tuple[str, str]]:
    """Get merged codec registry (built-in + plugins).

    Built-in codecs take precedence over plugins.
    """
    _ensure_plugins_discovered()

    # Start with built-in codecs (take precedence)
    merged = CODEC_REGISTRY.copy()

    # Add plugin codecs (don't override built-in)
    try:
        from ..plugins import get_plugin_registry

        registry = get_plugin_registry()
        for codec_id, value in registry._codecs.items():
            if codec_id not in merged:
                merged[codec_id] = value
    except Exception as e:
        format_detection_logger.warning("Failed to load plugin codecs: %s", e)

    return merged


# Built-in format metadata (derived from declarative descriptors in format_registry.py).
DATATYPE_REGISTRY: dict[str, tuple[str, str]] = build_datatype_registry()

CODEC_REGISTRY: dict[str, tuple[str, str]] = {
    "bz2": ("iterable.codecs.bz2codec", "BZIP2Codec"),
    "gz": ("iterable.codecs.gzipcodec", "GZIPCodec"),
    "lz4": ("iterable.codecs.lz4codec", "LZ4Codec"),
    "xz": ("iterable.codecs.lzmacodec", "LZMACodec"),
    "lzma": ("iterable.codecs.lzmacodec", "LZMACodec"),
    "zip": ("iterable.codecs.zipcodec", "ZIPCodec"),
    "br": ("iterable.codecs.brotlicodec", "BrotliCodec"),
    "zstd": ("iterable.codecs.zstdcodec", "ZSTDCodec"),
    "zst": ("iterable.codecs.zstdcodec", "ZSTDCodec"),
    "snappy": ("iterable.codecs.snappycodec", "SnappyCodec"),
    "sz": ("iterable.codecs.snappycodec", "SnappyCodec"),
    "lzo": ("iterable.codecs.lzocodec", "LZOCodec"),
    "lzop": ("iterable.codecs.lzocodec", "LZOCodec"),
    "7z": ("iterable.codecs.szipcodec", "SZipCodec"),
}

# Formats that are read-only (do not support write operations).
READ_ONLY_FORMATS: set[str] = build_read_only_formats()


def _datatype_class(ext: str) -> type[BaseIterable]:
    """Get datatype class for extension (with plugin support)."""
    registry = _get_format_registry()
    if ext not in registry:
        raise ValueError(f"Unknown format: {ext}")
    module_path, symbol = registry[ext]
    return cast(type[BaseIterable], _load_symbol(module_path, symbol))


def _codec_class(ext: str) -> type[BaseCodec]:
    """Get codec class for extension (with plugin support)."""
    registry = _get_codec_registry()
    if ext not in registry:
        raise ValueError(f"Unknown codec: {ext}")
    module_path, symbol = registry[ext]
    return cast(type[BaseCodec], _load_symbol(module_path, symbol))


class FileTypeResult(TypedDict, total=False):
    """Result of file type detection"""

    filename: str
    success: bool
    codec: type[BaseCodec] | None
    datatype: type[BaseIterable] | None
    confidence: float  # Confidence score 0.0-1.0, higher is more confident
    detection_method: str  # "filename", "magic_number", or "heuristic"


class CompressionResult(TypedDict):
    """Result of compression detection"""

    filename: str
    success: bool
    compression: type[BaseCodec] | None
    codec: type[BaseCodec] | None
    datatype: type[BaseIterable] | None


TEXT_DATA_TYPES: list[str] = build_text_data_types()

FLAT_TYPES: list[str] = build_flat_types()

ENGINES = ["internal", "duckdb"]

# DuckDB engine can read many file formats directly via DuckDB, but we keep this
# allowlist conservative and aligned with tests/docs.
DUCKDB_SUPPORTED_TYPES = ["csv", "jsonl", "ndjson", "json", "parquet"]
DUCKDB_SUPPORTED_CODECS = ["gz", "zstd", "zst"]


def is_flat(filename: str | None = None, filetype: str | None = None) -> bool:
    """Returns True if file is flat data file"""
    if filetype is not None:
        if filetype in FLAT_TYPES:
            return True
    elif filename is not None:
        parts = filename.lower().rsplit(".", 2)
        if len(parts) == 2:
            if parts[1] in FLAT_TYPES:
                return True
        elif len(parts) > 2:
            if parts[1] in FLAT_TYPES:
                return True
    return False


# Extensions that map to more than one unrelated format; content decides.
_AMBIGUOUS_EXTENSIONS: frozenset[str] = frozenset({"vcf"})


def _extension_is_ambiguous(filename: str) -> bool:
    """Return True if the filename's extension maps to multiple formats."""
    parts = filename.lower().rsplit(".", 2)
    if len(parts) < 2:
        return False
    ext = parts[-1]
    # An extension followed by a codec (e.g. foo.vcf.gz) keeps the format ext
    # in the penultimate position.
    if ext in _get_codec_registry() and len(parts) > 2:
        ext = parts[-2]
    return ext in _AMBIGUOUS_EXTENSIONS


def detect_file_type(filename: str, fileobj: IO[bytes] | None = None, debug: bool = False) -> FileTypeResult:
    """Detects file type and compression codec from filename and/or content

    Args:
        filename: Path to the file to detect
        fileobj: Optional file-like object for content-based detection
        debug: If True, enable verbose debug logging

    Returns:
        FileTypeResult dictionary with detection results

    Raises:
        ValueError: If filename is empty or invalid
    """
    if not filename:
        raise ValueError("Filename cannot be empty")

    if debug or is_debug_enabled():
        format_detection_logger.debug(f"Detecting file type for: {filename}")

    result: FileTypeResult = {
        "filename": filename,
        "success": False,
        "codec": None,
        "datatype": None,
        "confidence": 0.0,
        "detection_method": "none",
    }

    # First, try filename-based detection - High confidence (1.0)
    parts = filename.lower().rsplit(".", 2)
    if debug or is_debug_enabled():
        format_detection_logger.debug(f"File extension parts: {parts}")

    format_registry = _get_format_registry()
    codec_registry = _get_codec_registry()

    if len(parts) == 2:
        if parts[-1] in format_registry:
            result["datatype"] = _datatype_class(parts[-1])
            result["success"] = True
            result["confidence"] = 1.0
            result["detection_method"] = "filename"
            if debug or is_debug_enabled():
                format_detection_logger.debug(
                    f"Detected format from extension: {parts[-1]} (confidence: 1.0, method: filename)"
                )
    elif len(parts) > 2:
        if parts[-2] in format_registry and parts[-1] in codec_registry:
            result["datatype"] = _datatype_class(parts[-2])
            result["success"] = True
            result["codec"] = _codec_class(parts[-1])
            result["confidence"] = 1.0
            result["detection_method"] = "filename"
            if debug or is_debug_enabled():
                format_detection_logger.debug(
                    f"Detected format from extension: {parts[-2]} with codec {parts[-1]} "
                    f"(confidence: 1.0, method: filename)"
                )
        elif parts[-1] in format_registry:
            result["datatype"] = _datatype_class(parts[-1])
            result["success"] = True
            result["confidence"] = 1.0
            result["detection_method"] = "filename"
            if debug or is_debug_enabled():
                format_detection_logger.debug(
                    f"Detected format from extension: {parts[-1]} (confidence: 1.0, method: filename)"
                )

    # Some extensions are shared by unrelated formats (e.g. .vcf is both
    # genomic Variant Call Format and vCard). When the extension is ambiguous
    # and we have content to inspect, let content detection pick between them.
    if result["success"] and fileobj is not None and _extension_is_ambiguous(filename):
        detection_result = detect_file_type_from_content(fileobj)
        if detection_result:
            detected_format, confidence, method = detection_result
            format_registry = _get_format_registry()
            if detected_format and detected_format in format_registry:
                result["datatype"] = _datatype_class(detected_format)
                result["confidence"] = confidence
                result["detection_method"] = method

    # If filename detection failed and we have a file object, try content-based detection
    if not result["success"] and fileobj is not None:
        if debug or is_debug_enabled():
            format_detection_logger.debug("Extension detection failed, trying content-based detection")
        detection_result = detect_file_type_from_content(fileobj)
        if detection_result:
            detected_format, confidence, method = detection_result
            format_registry = _get_format_registry()
            if detected_format and detected_format in format_registry:
                result["datatype"] = _datatype_class(detected_format)
                result["success"] = True
                result["confidence"] = confidence
                result["detection_method"] = method
                if debug or is_debug_enabled():
                    format_detection_logger.debug(
                        f"Content-based detection: {detected_format} (confidence: {confidence:.2f}, method: {method})"
                    )

    if debug or is_debug_enabled():
        if result["success"]:
            format_detection_logger.debug(
                f"Detection successful: format={result['datatype'].__name__ if result['datatype'] else None}, "
                f"codec={result['codec'].__name__ if result['codec'] else None}, "
                f"confidence={result['confidence']:.2f}, method={result['detection_method']}"
            )
        else:
            format_detection_logger.debug("Detection failed: no matching format found")

    return result


def detect_compression(filename: str) -> CompressionResult:
    """Detects compression codec from filename

    Args:
        filename: Path to the file to detect compression for

    Returns:
        CompressionResult dictionary with detection results

    Raises:
        ValueError: If filename is empty or invalid
    """
    if not filename:
        raise ValueError("Filename cannot be empty")

    result: CompressionResult = {
        "filename": filename,
        "success": False,
        "compression": None,
        "codec": None,
        "datatype": None,
    }
    parts = filename.lower().rsplit(".", 2)
    codec_registry = _get_codec_registry()
    if len(parts) == 2:
        if parts[-1] in codec_registry:
            result["compression"] = _codec_class(parts[-1])
            result["success"] = True
    elif len(parts) > 2:
        if parts[-1] in codec_registry:
            result["compression"] = _codec_class(parts[-1])
            result["success"] = True
    return result


def detect_encoding_any(filename: str, limit: int = 1000000) -> dict[str, Any]:
    """Detects encoding of any data file including compressed

    Args:
        filename: Path to the file to detect encoding for
        limit: Maximum bytes to read for detection (default: 1000000)

    Returns:
        Dictionary with encoding detection results from chardet containing:
        - 'encoding': Detected encoding name
        - 'confidence': Confidence score (0.0 to 1.0)
        - 'language': Detected language (if available)

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If filename is empty
        IOError: If file cannot be read
    """
    if not filename:
        raise ValueError("Filename cannot be empty")

    import os

    if not os.path.exists(filename):
        raise FileNotFoundError(
            f"File not found: '{filename}'. Please check that the file exists and the path is correct."
        )

    result = detect_file_type(filename)
    fileobj = None
    codec = None

    try:
        if result["success"]:
            if result["codec"] is not None:
                try:
                    codec = result["codec"](filename, open_it=True)
                    fileobj = codec.fileobj()
                except Exception as e:
                    raise OSError(
                        f"Failed to open compressed file '{filename}' with codec '{result['codec']}'. Error: {str(e)}"
                    ) from e
        if fileobj is None:
            try:
                fileobj = open(filename, "rb")
            except OSError as e:
                raise OSError(
                    f"Cannot read file '{filename}'. "
                    f"Please check file permissions and that the file is not corrupted. "
                    f"Error: {str(e)}"
                ) from e

        chunk = fileobj.read(limit)
        if not chunk:
            raise ValueError(f"File '{filename}' appears to be empty")

        detected = chardet.detect(chunk)
        if not detected or detected.get("encoding") is None:
            raise ValueError(
                f"Could not detect encoding for file '{filename}'. "
                f"The file may be binary or use an unsupported encoding."
            )

        return cast(dict[str, Any], detected)
    finally:
        if codec is not None:
            try:
                codec.close()
            except Exception:
                pass
        elif fileobj is not None:
            try:
                fileobj.close()
            except Exception:
                pass


_LAZY_OPEN_NAMES = frozenset(
    {
        "CLOUD_STORAGE_SCHEMES",
        "_get_cloud_backend",
        "_is_cloud_storage_uri",
        "_open_stream_iterable",
        "open_iterable",
    }
)
_LAZY_CONVERT_NAMES = frozenset({"bulk_convert", "convert"})


def __getattr__(name: str) -> Any:
    if name in _LAZY_OPEN_NAMES:
        from . import open_iterable as _open_mod

        return getattr(_open_mod, name)
    if name in _LAZY_CONVERT_NAMES:
        from ..convert.core import bulk_convert, convert

        return bulk_convert if name == "bulk_convert" else convert
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _LAZY_OPEN_NAMES | _LAZY_CONVERT_NAMES)


__all__ = ["open_iterable", "detect_file_type", "detect_file_type_from_content", "convert", "bulk_convert"]  # noqa: F822
