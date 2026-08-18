"""Open files, streams, cloud URIs, and database sources as iterables."""

from __future__ import annotations

import os
import warnings
from collections.abc import Callable
from typing import Any, Literal, Protocol, cast, runtime_checkable

from ..base import BaseIterable
from ..exceptions import FormatDetectionError, IterableDataError, ReadError
from ..types import CodecArgs, IterableArgs
from .debug import file_io_logger, format_detection_logger, is_debug_enabled
from .detect import (
    DATATYPE_REGISTRY,
    DUCKDB_SUPPORTED_CODECS,
    DUCKDB_SUPPORTED_TYPES,
    FileTypeResult,
    _datatype_class,
    _extension_is_ambiguous,
    _get_codec_registry,
    _get_format_registry,
    detect_file_type,
)

# Cloud storage URI schemes supported
CLOUD_STORAGE_SCHEMES = {
    "s3": "s3fs",
    "s3a": "s3fs",
    "gs": "gcsfs",
    "gcs": "gcsfs",
    "az": "adlfs",
    "abfs": "adlfs",
    "abfss": "adlfs",
}


@runtime_checkable
class _FileLike(Protocol):
    def read(self, size: int = -1, /) -> bytes | str: ...


OpenFilename = str | os.PathLike[str] | _FileLike

# Format classes accept heterogeneous constructor kwargs (filename, stream, codec, ...).
_FormatConstructor = Callable[..., BaseIterable]


def _instantiate_datatype(datatype: type[BaseIterable], **kwargs: Any) -> BaseIterable:
    constructor = cast(_FormatConstructor, datatype)
    return constructor(**kwargs)


def _is_cloud_storage_uri(filename: str) -> bool:
    """Check if filename is a cloud storage URI."""
    if not filename or not isinstance(filename, str):
        return False
    return any(filename.startswith(f"{scheme}://") for scheme in CLOUD_STORAGE_SCHEMES)


def _get_cloud_backend(filename: str) -> str | None:
    """Get the required backend package for a cloud storage URI."""
    if not _is_cloud_storage_uri(filename):
        return None
    for scheme, backend in CLOUD_STORAGE_SCHEMES.items():
        if filename.startswith(f"{scheme}://"):
            return backend
    return None


def _resolve_stream_datatype(stream: Any, normalized_mode: str, debug: bool) -> type[BaseIterable]:
    """Detect the format for a stream from content, falling back to CSV with a warning."""
    if normalized_mode != "r":
        return _datatype_class("csv")
    detection_failure = "stream is not seekable, so content cannot be inspected"
    try:
        if hasattr(stream, "seekable") and stream.seekable():
            pos = stream.tell()
            result = detect_file_type("stream", fileobj=stream, debug=debug or is_debug_enabled())
            try:
                stream.seek(pos)
            except (OSError, ValueError):
                pass
            if result.get("success") and result["datatype"] is not None:
                return result["datatype"]
            detection_failure = "content-based detection did not recognize the format"
    except Exception as e:
        detection_failure = f"content-based detection failed with {type(e).__name__}: {e}"
    warnings.warn(
        f"Could not detect the stream format ({detection_failure}); assuming CSV. "
        "Pass format='...' to open_iterable() to select the format explicitly.",
        UserWarning,
        stacklevel=3,
    )
    return _datatype_class("csv")


def _explicit_stream_datatype(explicit_format: str) -> type[BaseIterable]:
    """Resolve an explicit format hint for a stream, or raise if unknown."""
    format_id = explicit_format.lower()
    registry = _get_format_registry()
    if format_id not in registry:
        from ..exceptions import FormatNotSupportedError

        raise FormatNotSupportedError(
            format_id=format_id,
            reason=f"Unknown format. Supported formats: {', '.join(sorted(set(registry.keys())))}",
        )
    return _datatype_class(format_id)


def _open_stream_iterable(
    stream: Any,
    mode: str = "r",
    engine: str = "internal",
    iterableargs: IterableArgs | None = None,
    debug: bool = False,
) -> BaseIterable:
    """Open an iterable backed by an in-memory/file-like stream."""
    if iterableargs is None:
        iterableargs = {}
    iterableargs.setdefault("_debug", debug or is_debug_enabled())

    normalized_mode = "r" if mode in ["r", "rb"] else "w"

    explicit_format = iterableargs.get("format")
    if explicit_format:
        datatype = _explicit_stream_datatype(explicit_format)
    else:
        datatype = _resolve_stream_datatype(stream, normalized_mode, debug)

    try:
        return _instantiate_datatype(datatype, stream=stream, mode=normalized_mode, options=iterableargs)
    except (IterableDataError, OSError, ValueError, TypeError):
        raise
    except Exception as e:
        raise ReadError(
            f"Failed to open stream with format '{datatype.__name__}'. Error: {str(e)}",
            error_code="STREAM_OPEN_FAILED",
        ) from e


def _maybe_open_database_engine(engine: str, filename: str | None, iterableargs: IterableArgs) -> BaseIterable | None:
    """Open a database-backed iterable when ``engine`` names a DB driver.

    Returns ``None`` when ``engine`` is not a database engine so the caller
    falls through to file-based handling.
    """
    try:
        from ..db.iterable import DatabaseIterable
        from .detect import get_driver, is_database_engine

        if is_database_engine(engine):
            driver_class = get_driver(engine)
            if driver_class is None:
                raise ValueError(f"Database engine '{engine}' is not available. Install the required driver.")
            driver = driver_class(source=filename, **iterableargs)
            return cast(BaseIterable, DatabaseIterable(driver))
    except ImportError:
        pass
    return None


def _open_cloud_stream(filename: str, mode: str, storage_options: dict[str, Any]) -> Any:
    """Open a file-like stream for a cloud storage URI via fsspec."""
    try:
        import fsspec  # type: ignore[import-not-found]
    except ImportError:
        raise ImportError("Cloud storage support requires 'fsspec'. Install it with: pip install fsspec") from None

    backend = _get_cloud_backend(filename)
    if backend:
        try:
            __import__(backend)
        except ImportError:
            raise ImportError(
                f"Cloud storage URI '{filename}' requires '{backend}'. Install it with: pip install {backend}"
            ) from None

    try:
        fsspec_mode = "rb" if mode in ["r", "rb"] else "wb"
        handle = fsspec.open(filename, mode=fsspec_mode, **storage_options)
        return handle.open()
    except Exception as e:
        if "NoCredentialsError" in str(type(e).__name__) or "credentials" in str(e).lower():
            raise ReadError(
                f"Authentication failed for cloud storage URI '{filename}'. "
                f"Please configure credentials via environment variables or storage_options. "
                f"Error: {str(e)}",
                filename=filename,
                error_code="CLOUD_AUTH_FAILED",
            ) from e
        if "NoSuchKey" in str(type(e).__name__) or "not found" in str(e).lower():
            raise FileNotFoundError(
                f"File not found in cloud storage: '{filename}'. "
                f"Please check that the file exists and the path is correct."
            ) from e
        raise ReadError(
            f"Failed to open cloud storage URI '{filename}': {str(e)}",
            filename=filename,
            error_code="CLOUD_OPEN_FAILED",
        ) from e


def _content_detect(filename: str, is_cloud_uri: bool, cloud_stream: Any, debug: bool) -> FileTypeResult | None:
    """Run content-based detection against a local or cloud stream, if possible."""
    try:
        if is_cloud_uri and cloud_stream is not None:
            try:
                if hasattr(cloud_stream, "seekable") and cloud_stream.seekable():
                    pos = cloud_stream.tell()
                    result = detect_file_type(filename, fileobj=cloud_stream, debug=debug)
                    cloud_stream.seek(pos)
                    return result
            except Exception:
                return None
        else:
            with open(filename, "rb") as f:
                return detect_file_type(filename, fileobj=f, debug=debug)
    except OSError:
        return None
    return None


def _apply_explicit_format(result: FileTypeResult, iterableargs: IterableArgs) -> None:
    """Override detection with an explicit ``format`` hint when provided."""
    explicit_format = iterableargs.get("format")
    if not explicit_format:
        return
    format_id = explicit_format.lower()
    if format_id in _get_format_registry():
        result["datatype"] = _datatype_class(format_id)
        result["success"] = True
        result["codec"] = None
        result["confidence"] = 1.0
        result["detection_method"] = "explicit"


def _disambiguate_extension(result: FileTypeResult, filename: str, debug_enabled: bool) -> FileTypeResult:
    """For a shared extension (e.g. .vcf), let content pick the concrete format."""
    if not _extension_is_ambiguous(filename):
        return result
    refined = _content_detect(filename, is_cloud_uri=False, cloud_stream=None, debug=debug_enabled)
    if refined is not None and refined.get("success"):
        return refined
    return result


def _refine_detection_with_content(
    result: FileTypeResult,
    filename: str,
    *,
    normalized_mode: str,
    is_cloud_uri: bool,
    cloud_stream: Any,
    file_missing: bool,
    debug_enabled: bool,
) -> FileTypeResult:
    """Refine an extension-based detection by inspecting file content."""
    readable_local = normalized_mode == "r" and not file_missing and not is_cloud_uri

    if result["success"]:
        if readable_local:
            return _disambiguate_extension(result, filename, debug_enabled)
        return result

    if normalized_mode == "r" and not file_missing:
        if debug_enabled:
            format_detection_logger.debug("Filename detection failed, attempting content-based detection")
        refined = _content_detect(filename, is_cloud_uri=is_cloud_uri, cloud_stream=cloud_stream, debug=debug_enabled)
        if refined is not None:
            return refined
    return result


def _detect_source_format(
    filename: str,
    normalized_mode: str,
    is_cloud_uri: bool,
    cloud_stream: Any,
    file_missing: bool,
    iterableargs: IterableArgs,
    debug: bool,
) -> FileTypeResult:
    """Detect the format via extension, content disambiguation, and explicit hint."""
    debug_enabled = debug or is_debug_enabled()
    result = detect_file_type(filename, debug=debug_enabled)
    result = _refine_detection_with_content(
        result,
        filename,
        normalized_mode=normalized_mode,
        is_cloud_uri=is_cloud_uri,
        cloud_stream=cloud_stream,
        file_missing=file_missing,
        debug_enabled=debug_enabled,
    )

    if file_missing and result["success"]:
        raise FileNotFoundError(
            f"File not found: '{filename}'. Please check that the file exists and the path is correct."
        )

    # Explicit format always wins (e.g. format=ducklake on a .duckdb catalog path).
    _apply_explicit_format(result, iterableargs)

    if not result["success"]:
        from ..exceptions import FormatNotSupportedError

        ext = os.path.splitext(filename)[1].lstrip(".").lower() or "unknown"
        raise FormatNotSupportedError(
            format_id=ext,
            reason=f"Could not detect file type from filename or content for file: {filename}. "
            f"Supported formats: {', '.join(sorted(set(DATATYPE_REGISTRY.keys())))}",
        )

    return result


def _resolve_type_and_codec(
    filename: str, result: FileTypeResult, iterableargs: IterableArgs
) -> tuple[str | None, str | None]:
    """Derive the detected filetype/codec labels used for engine checks and logs."""
    if result.get("detection_method") == "explicit":
        return (iterableargs.get("format", "").lower() or None, None)

    parts = filename.lower().rsplit(".", 2)
    codec_registry = _get_codec_registry()
    if len(parts) == 2:
        return (parts[-1], None)
    if len(parts) > 2:
        if parts[-1] in codec_registry:
            return (parts[-2], parts[-1])
        return (parts[-1], None)
    return (None, None)


def _validate_engine_support(engine: str, detected_filetype: str | None, detected_codec: str | None) -> None:
    """Reject file/codec combinations the requested engine cannot handle."""
    if engine != "duckdb":
        return
    if detected_filetype not in DUCKDB_SUPPORTED_TYPES:
        raise ValueError(
            f"DuckDB engine does not support file type '{detected_filetype}'. "
            f"Supported types: {', '.join(DUCKDB_SUPPORTED_TYPES)}. "
            f"Use engine='internal' for this file type."
        )
    if detected_codec is not None and detected_codec not in DUCKDB_SUPPORTED_CODECS:
        raise ValueError(
            f"DuckDB engine does not support compression codec '{detected_codec}'. "
            f"Supported codecs: {', '.join(DUCKDB_SUPPORTED_CODECS)}. "
            f"Use engine='internal' for this compression codec."
        )


def _build_source(
    datatype_cls: type[BaseIterable],
    result: FileTypeResult,
    *,
    filename: str,
    is_cloud_uri: bool,
    cloud_stream: Any,
    engine: str,
    normalized_mode: str,
    mode: str,
    iterableargs: IterableArgs,
    codecargs: CodecArgs,
) -> BaseIterable:
    """Construct the concrete iterable for the resolved format/codec/engine."""
    codec_cls = result["codec"]
    if is_cloud_uri and cloud_stream is not None:
        if codec_cls is not None and engine != "duckdb":
            codec = codec_cls(filename=filename, fileobj=cloud_stream, mode=mode, options=codecargs)
            return _instantiate_datatype(datatype_cls, codec=codec, mode=normalized_mode, options=iterableargs)
        if engine == "duckdb":
            raise ValueError(
                "DuckDB engine does not support cloud storage URIs. Use engine='internal' for cloud storage files."
            )
        return _instantiate_datatype(datatype_cls, stream=cloud_stream, mode=normalized_mode, options=iterableargs)
    if codec_cls is not None and engine != "duckdb":
        codec = codec_cls(filename=filename, mode=mode, options=codecargs)
        return _instantiate_datatype(datatype_cls, codec=codec, mode=normalized_mode, options=iterableargs)
    if engine == "duckdb":
        try:
            from ..engines.duckdb import DuckDBEngineIterable
        except ImportError as e:
            raise ImportError(
                "DuckDB engine requires the 'duckdb' dependency. Install it with: pip install duckdb"
            ) from e
        return cast(
            BaseIterable,
            DuckDBEngineIterable(filename=filename, mode=normalized_mode, options=iterableargs),
        )
    return _instantiate_datatype(datatype_cls, filename=filename, mode=normalized_mode, options=iterableargs)


def _instantiate_source(
    datatype_cls: type[BaseIterable],
    result: FileTypeResult,
    *,
    filename: str,
    is_cloud_uri: bool,
    cloud_stream: Any,
    engine: str,
    normalized_mode: str,
    mode: str,
    iterableargs: IterableArgs,
    codecargs: CodecArgs,
    detected_filetype: str | None,
    detected_codec: str | None,
    debug: bool,
) -> BaseIterable:
    """Construct the concrete iterable, wrapping unexpected failures with context."""
    try:
        return _build_source(
            datatype_cls,
            result,
            filename=filename,
            is_cloud_uri=is_cloud_uri,
            cloud_stream=cloud_stream,
            engine=engine,
            normalized_mode=normalized_mode,
            mode=mode,
            iterableargs=iterableargs,
            codecargs=codecargs,
        )
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"File not found: '{filename}'. Please check that the file exists and the path is correct."
        ) from e
    except (OSError, LookupError, IterableDataError, ImportError, ValueError, TypeError):
        raise
    except Exception as e:
        if debug or is_debug_enabled():
            file_io_logger.error(f"Failed to open file '{filename}': {e}", exc_info=True)
        raise ReadError(
            f"Failed to open file '{filename}' with format '{datatype_cls.__name__}' "
            f"(detected type: '{detected_filetype}', codec: '{detected_codec or 'none'}'). "
            f"Error: {str(e)}",
            filename=filename,
            error_code="OPEN_FAILED",
        ) from e


def _looks_like_stream(filename: OpenFilename | None) -> bool:
    """True when a filename argument is actually a file-like object."""
    return (
        filename is not None
        and not isinstance(filename, (str, bytes))
        and not hasattr(filename, "__fspath__")
        and hasattr(filename, "read")
    )


def _normalize_open_inputs(
    filename: OpenFilename | None,
    stream: Any | None,
    iterableargs: IterableArgs | None,
    options: IterableArgs | None,
    format: str | None,
) -> tuple[str | None, Any | None, IterableArgs]:
    """Coerce filename/stream/args into their canonical forms.

    Handles the ``options`` merge, the file-like-``filename`` -> ``stream``
    swap, the explicit ``format`` injection, and PathLike coercion.
    """
    if options is not None:
        iterableargs = {**(iterableargs or {}), **options}

    if _looks_like_stream(filename):
        stream = filename
        filename = None

    if format is not None:
        iterableargs = {**(iterableargs or {}), "format": format}

    resolved_filename: str | None
    if filename is not None and not isinstance(filename, str):
        resolved_filename = os.fspath(cast(os.PathLike[str], filename))
    else:
        resolved_filename = filename

    return resolved_filename, stream, iterableargs or {}


def _open_file_iterable(
    filename: str,
    mode: Literal["r", "w", "rb", "wb"],
    engine: str,
    codecargs: CodecArgs | None,
    iterableargs: IterableArgs,
    debug: bool,
) -> BaseIterable:
    """Open a filesystem/cloud-backed iterable (non-stream path)."""
    db_iterable = _maybe_open_database_engine(engine, filename, iterableargs)
    if db_iterable is not None:
        return db_iterable

    if engine not in ["internal", "duckdb"]:
        raise ValueError(f"Engine must be 'internal', 'duckdb', or a registered database engine, got '{engine}'")

    normalized_mode = "r" if mode in ["r", "rb"] else "w"

    if codecargs is None:
        codecargs = {}

    is_cloud_uri = _is_cloud_storage_uri(filename)
    cloud_stream = None
    if is_cloud_uri:
        cloud_stream = _open_cloud_stream(filename, mode, iterableargs.get("storage_options", {}))

    file_missing = normalized_mode == "r" and not is_cloud_uri and not os.path.exists(filename)

    result = _detect_source_format(
        filename,
        normalized_mode=normalized_mode,
        is_cloud_uri=is_cloud_uri,
        cloud_stream=cloud_stream,
        file_missing=file_missing,
        iterableargs=iterableargs,
        debug=debug,
    )

    return _finalize_source(
        result,
        filename=filename,
        mode=mode,
        engine=engine,
        normalized_mode=normalized_mode,
        is_cloud_uri=is_cloud_uri,
        cloud_stream=cloud_stream,
        iterableargs=iterableargs,
        codecargs=codecargs,
        debug=debug,
    )


def _finalize_source(
    result: FileTypeResult,
    *,
    filename: str,
    mode: Literal["r", "w", "rb", "wb"],
    engine: str,
    normalized_mode: str,
    is_cloud_uri: bool,
    cloud_stream: Any,
    iterableargs: IterableArgs,
    codecargs: CodecArgs,
    debug: bool,
) -> BaseIterable:
    """Validate engine support and instantiate the resolved iterable."""
    detected_filetype, detected_codec = _resolve_type_and_codec(filename, result, iterableargs)
    _validate_engine_support(engine, detected_filetype, detected_codec)

    datatype_cls = result["datatype"]
    if datatype_cls is None:
        raise FormatDetectionError(
            filename=filename,
            reason="Internal error: file type detection succeeded but datatype class is missing",
        )

    if debug or is_debug_enabled():
        codec_name = result["codec"].__name__ if result["codec"] else "none"
        file_io_logger.debug(f"Creating iterable: format={datatype_cls.__name__}, codec={codec_name}, engine={engine}")

    iterable = _instantiate_source(
        datatype_cls,
        result,
        filename=filename,
        is_cloud_uri=is_cloud_uri,
        cloud_stream=cloud_stream,
        engine=engine,
        normalized_mode=normalized_mode,
        mode=mode,
        iterableargs=iterableargs,
        codecargs=codecargs,
        detected_filetype=detected_filetype,
        detected_codec=detected_codec,
        debug=debug,
    )

    if debug or is_debug_enabled():
        file_io_logger.debug(f"Successfully opened file: {filename}")

    return iterable


def open_iterable(
    filename: OpenFilename | None = None,
    mode: Literal["r", "w", "rb", "wb"] = "r",
    engine: str = "internal",
    codecargs: CodecArgs | None = None,
    iterableargs: IterableArgs | None = None,
    debug: bool = False,
    *,
    options: IterableArgs | None = None,
    stream: Any | None = None,
    format: str | None = None,
) -> BaseIterable:
    """Opens file and returns iterable object."""
    filename, stream, iterableargs = _normalize_open_inputs(filename, stream, iterableargs, options, format)

    if stream is not None:
        return _open_stream_iterable(stream, mode=mode, engine=engine, iterableargs=iterableargs, debug=debug)

    if debug or is_debug_enabled():
        file_io_logger.debug(f"Opening file: {filename} (mode: {mode}, engine: {engine})")

    if not filename:
        raise ValueError("Filename cannot be empty")

    if debug:
        from .debug import enable_debug_mode

        enable_debug_mode()

    iterableargs["_debug"] = debug or is_debug_enabled()

    on_error = iterableargs.get("on_error", "raise")
    if on_error not in ("raise", "skip", "warn"):
        raise ValueError(f"Invalid 'on_error' value: '{on_error}'. Valid values are: 'raise', 'skip', 'warn'")

    return _open_file_iterable(filename, mode, engine, codecargs, iterableargs, debug)
