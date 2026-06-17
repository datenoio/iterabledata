"""Open files, streams, cloud URIs, and database sources as iterables."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, Literal, Protocol, cast, runtime_checkable

from ..base import BaseIterable
from ..exceptions import IterableDataError
from ..types import CodecArgs, IterableArgs
from .debug import file_io_logger, format_detection_logger, is_debug_enabled
from .detect import (
    DATATYPE_REGISTRY,
    DUCKDB_SUPPORTED_CODECS,
    DUCKDB_SUPPORTED_TYPES,
    _datatype_class,
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
    datatype: type[BaseIterable] | None = None

    if explicit_format:
        format_id = explicit_format.lower()
        registry = _get_format_registry()
        if format_id not in registry:
            from ..exceptions import FormatNotSupportedError

            raise FormatNotSupportedError(
                format_id=format_id,
                reason=f"Unknown format. Supported formats: {', '.join(sorted(set(registry.keys())))}",
            )
        datatype = _datatype_class(format_id)
    elif normalized_mode == "r":
        try:
            if hasattr(stream, "seekable") and stream.seekable():
                pos = stream.tell()
                result = detect_file_type("stream", fileobj=stream, debug=debug or is_debug_enabled())
                try:
                    stream.seek(pos)
                except (OSError, ValueError):
                    pass
                if result.get("success"):
                    datatype = result["datatype"]
        except Exception:
            pass

    if datatype is None:
        datatype = _datatype_class("csv")

    try:
        return _instantiate_datatype(datatype, stream=stream, mode=normalized_mode, options=iterableargs)
    except IterableDataError:
        raise
    except (OSError, ValueError, TypeError):
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to open stream with format '{datatype.__name__}'. Error: {str(e)}") from e


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
    if options is not None:
        iterableargs = {**(iterableargs or {}), **options}

    if (
        filename is not None
        and not isinstance(filename, (str, bytes))
        and not hasattr(filename, "__fspath__")
        and hasattr(filename, "read")
    ):
        stream = filename
        filename = None

    if format is not None:
        iterableargs = {**(iterableargs or {}), "format": format}

    if stream is not None:
        return _open_stream_iterable(
            stream,
            mode=mode,
            engine=engine,
            iterableargs=iterableargs,
            debug=debug,
        )

    if filename is not None and not isinstance(filename, str):
        filename = os.fspath(cast(os.PathLike[str], filename))

    if debug or is_debug_enabled():
        file_io_logger.debug(f"Opening file: {filename} (mode: {mode}, engine: {engine})")

    if not filename:
        raise ValueError("Filename cannot be empty")

    if debug:
        from .debug import enable_debug_mode

        enable_debug_mode()

    if iterableargs is None:
        iterableargs = {}
    iterableargs["_debug"] = debug or is_debug_enabled()

    on_error = iterableargs.get("on_error", "raise")
    if on_error not in ("raise", "skip", "warn"):
        raise ValueError(f"Invalid 'on_error' value: '{on_error}'. Valid values are: 'raise', 'skip', 'warn'")

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

    if engine not in ["internal", "duckdb"]:
        raise ValueError(f"Engine must be 'internal', 'duckdb', or a registered database engine, got '{engine}'")

    normalized_mode = "r" if mode in ["r", "rb"] else "w"

    if codecargs is None:
        codecargs = {}

    is_cloud_uri = _is_cloud_storage_uri(filename)
    cloud_stream = None
    storage_options = iterableargs.get("storage_options", {})

    if is_cloud_uri:
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
            cloud_stream = fsspec.open(filename, mode=fsspec_mode, **storage_options)
            cloud_stream = cloud_stream.open()
        except Exception as e:
            if "NoCredentialsError" in str(type(e).__name__) or "credentials" in str(e).lower():
                raise RuntimeError(
                    f"Authentication failed for cloud storage URI '{filename}'. "
                    f"Please configure credentials via environment variables or storage_options. "
                    f"Error: {str(e)}"
                ) from e
            if "NoSuchKey" in str(type(e).__name__) or "not found" in str(e).lower():
                raise FileNotFoundError(
                    f"File not found in cloud storage: '{filename}'. "
                    f"Please check that the file exists and the path is correct."
                ) from e
            raise RuntimeError(f"Failed to open cloud storage URI '{filename}': {str(e)}") from e

    file_missing = normalized_mode == "r" and not is_cloud_uri and not os.path.exists(filename)

    result = detect_file_type(filename, debug=debug or is_debug_enabled())

    if file_missing and result["success"]:
        raise FileNotFoundError(
            f"File not found: '{filename}'. Please check that the file exists and the path is correct."
        )

    if not result["success"] and normalized_mode == "r" and not file_missing:
        if debug or is_debug_enabled():
            format_detection_logger.debug("Filename detection failed, attempting content-based detection")
        try:
            if is_cloud_uri and cloud_stream is not None:
                try:
                    if hasattr(cloud_stream, "seekable") and cloud_stream.seekable():
                        pos = cloud_stream.tell()
                        result = detect_file_type(filename, fileobj=cloud_stream, debug=debug or is_debug_enabled())
                        cloud_stream.seek(pos)
                except Exception:
                    pass
            else:
                with open(filename, "rb") as f:
                    result = detect_file_type(filename, fileobj=f, debug=debug or is_debug_enabled())
        except OSError:
            pass

    if not result["success"]:
        explicit_format = iterableargs.get("format")
        if explicit_format:
            format_id = explicit_format.lower()
            format_registry = _get_format_registry()
            if format_id in format_registry:
                result["datatype"] = _datatype_class(format_id)
                result["success"] = True
                result["codec"] = None
                result["confidence"] = 1.0
                result["detection_method"] = "explicit"

        if not result["success"]:
            from ..exceptions import FormatNotSupportedError

            ext = os.path.splitext(filename)[1].lstrip(".").lower() or "unknown"
            raise FormatNotSupportedError(
                format_id=ext,
                reason=f"Could not detect file type from filename or content for file: {filename}. "
                f"Supported formats: {', '.join(sorted(set(DATATYPE_REGISTRY.keys())))}",
            )

    if result.get("detection_method") == "explicit":
        detected_filetype = iterableargs.get("format", "").lower() or None
        detected_codec = None
    else:
        parts = filename.lower().rsplit(".", 2)
        detected_filetype = None
        detected_codec = None
        codec_registry = _get_codec_registry()
        if len(parts) == 2:
            detected_filetype = parts[-1]
        elif len(parts) > 2:
            detected_filetype = parts[-2] if parts[-1] in codec_registry else parts[-1]
            detected_codec = parts[-1] if parts[-1] in codec_registry else None

    if engine == "duckdb":
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

    datatype_cls = result["datatype"]
    if datatype_cls is None:
        raise RuntimeError("Internal error: file type detection succeeded but datatype class is missing")

    datatype_name = datatype_cls.__name__

    if debug or is_debug_enabled():
        codec_name = result["codec"].__name__ if result["codec"] else "none"
        file_io_logger.debug(f"Creating iterable: format={datatype_name}, codec={codec_name}, engine={engine}")

    try:
        if is_cloud_uri and cloud_stream is not None:
            if result["codec"] is not None and engine != "duckdb":
                codec = result["codec"](filename=filename, fileobj=cloud_stream, mode=mode, options=codecargs)
                iterable = _instantiate_datatype(datatype_cls, codec=codec, mode=normalized_mode, options=iterableargs)
            elif engine == "duckdb":
                raise ValueError(
                    "DuckDB engine does not support cloud storage URIs. Use engine='internal' for cloud storage files."
                )
            else:
                iterable = _instantiate_datatype(
                    datatype_cls, stream=cloud_stream, mode=normalized_mode, options=iterableargs
                )
        elif result["codec"] is not None and engine != "duckdb":
            codec = result["codec"](filename=filename, mode=mode, options=codecargs)
            iterable = _instantiate_datatype(datatype_cls, codec=codec, mode=normalized_mode, options=iterableargs)
        elif engine == "duckdb":
            try:
                from ..engines.duckdb import DuckDBEngineIterable
            except ImportError as e:
                raise ImportError(
                    "DuckDB engine requires the 'duckdb' dependency. Install it with: pip install duckdb"
                ) from e
            iterable = DuckDBEngineIterable(filename=filename, mode=normalized_mode, options=iterableargs)
        else:
            iterable = _instantiate_datatype(
                datatype_cls, filename=filename, mode=normalized_mode, options=iterableargs
            )
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"File not found: '{filename}'. Please check that the file exists and the path is correct."
        ) from e
    except (OSError, LookupError):
        raise
    except IterableDataError:
        raise
    except ImportError:
        raise
    except Exception as e:
        if debug or is_debug_enabled():
            file_io_logger.error(f"Failed to open file '{filename}': {e}", exc_info=True)
        raise RuntimeError(
            f"Failed to open file '{filename}' with format '{datatype_name}' "
            f"(detected type: '{detected_filetype}', codec: '{detected_codec or 'none'}'). "
            f"Error: {str(e)}"
        ) from e

    if debug or is_debug_enabled():
        file_io_logger.debug(f"Successfully opened file: {filename}")

    return iterable
