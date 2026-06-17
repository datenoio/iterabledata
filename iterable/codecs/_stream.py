"""Shared helpers for stream-wrapping compression codecs."""

from __future__ import annotations

from typing import Any


def get_underlying_fileobj(codec: Any, wrapper_type: type | tuple[type, ...]) -> Any | None:
    """Return the raw file object to wrap, preserving ``_original_fileobj`` across reset."""
    original = getattr(codec, "_original_fileobj", None)
    if original is not None:
        return original
    fileobj = codec._fileobj
    if fileobj is not None and not isinstance(fileobj, wrapper_type):
        codec._original_fileobj = fileobj
        return fileobj
    return None
