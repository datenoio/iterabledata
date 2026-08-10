"""File-level metadata extraction for documentation generation.

Computes cheap structural metadata (name, size, content hash, format, encoding,
table count) used by the ``general`` documentation block and the ``source``
descriptor, plus helpers for multi-table inputs.
"""

from __future__ import annotations

import collections.abc
import hashlib
import os
from typing import Any

from ..helpers.detect import open_iterable
from ..types import Row

_HASH_CHUNK = 1024 * 1024  # 1 MB


def file_hash(path: str, algo: str = "sha256") -> str | None:
    """Compute a content hash for a file path. Returns None if unreadable."""
    try:
        hasher = hashlib.new(algo)
    except (ValueError, TypeError):
        hasher = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(_HASH_CHUNK), b""):
                hasher.update(chunk)
    except OSError:
        return None
    return hasher.hexdigest()


def detect_format(path: str) -> str | None:
    """Best-effort format identifier from a file path extension."""
    base = os.path.basename(path).lower()
    parts = base.rsplit(".", 2)
    if len(parts) >= 2:
        # Skip a trailing compression codec extension when a data extension precedes it.
        codecs = {"gz", "bz2", "xz", "zst", "zstd", "lz4", "lzo", "sz", "br", "snappy", "zip"}
        if len(parts) == 3 and parts[-1] in codecs:
            return parts[-2]
        return parts[-1]
    return None


def detect_text_encoding(path: str) -> str | None:
    """Best-effort text encoding detection; returns None on failure."""
    try:
        from ..helpers.detect import detect_encoding_any

        result = detect_encoding_any(path)
        return result.get("encoding")
    except Exception:
        return None


def list_tables(source: str) -> list[str] | None:
    """Return available tables/sheets for a multi-table file, or None."""
    try:
        obj = open_iterable(source)
    except Exception:
        return None
    try:
        if hasattr(obj, "list_tables"):
            return obj.list_tables()
    except Exception:
        return None
    finally:
        if hasattr(obj, "close"):
            try:
                obj.close()
            except Exception:
                pass
    return None


def count_records(iterable: collections.abc.Iterable[Row] | str) -> int | None:
    """Count records by streaming. Returns None on error.

    Note: this performs a full pass; callers should avoid it for very large inputs.
    """
    opened = None
    try:
        if isinstance(iterable, str):
            opened = open_iterable(iterable)
            source: collections.abc.Iterable[Row] = opened
        else:
            source = iterable
        return sum(1 for _ in source)
    except Exception:
        return None
    finally:
        if opened is not None and hasattr(opened, "close"):
            try:
                opened.close()
            except Exception:
                pass


def file_metadata(
    source: str,
    *,
    compute_hash: bool = True,
    hash_algo: str = "sha256",
    detect_encoding: bool = True,
) -> dict[str, Any]:
    """Collect file-level metadata for a path.

    Returns a dict with keys: file_name, file_size, file_hash, hash_algo, format,
    encoding, tables, table_count. Missing values are None.
    """
    meta: dict[str, Any] = {
        "file_name": os.path.basename(source) if source else None,
        "file_size": None,
        "file_hash": None,
        "hash_algo": hash_algo,
        "format": detect_format(source) if source else None,
        "encoding": None,
        "tables": None,
        "table_count": None,
    }

    if source and os.path.exists(source):
        try:
            meta["file_size"] = os.path.getsize(source)
        except OSError:
            pass
        if compute_hash:
            meta["file_hash"] = file_hash(source, hash_algo)
        if detect_encoding:
            meta["encoding"] = detect_text_encoding(source)

    tables = list_tables(source) if source else None
    if tables:
        meta["tables"] = tables
        meta["table_count"] = len(tables)
    return meta


def open_table(source: str, table: str) -> Any:
    """Open a specific table/sheet of a multi-table file by name.

    Sheets are opened by ``page`` index. SQLite tables are opened by ``table``
    name. Falls back to the default open when the name cannot be resolved.

    Important: Excel formats ignore unknown ``table=`` options and silently open
    page 0, so we must not try ``table`` before ``page`` for sheet-based files.
    """
    tables = list_tables(source)
    if tables and table in tables:
        index = tables.index(table)
        probe = open_iterable(source)
        try:
            datatype_id = type(probe).id()
        finally:
            close = getattr(probe, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass
        if datatype_id in {"xlsx", "xls", "ods"}:
            return open_iterable(source, iterableargs={"page": index})
        return open_iterable(source, iterableargs={"table": table})
    return open_iterable(source)
