"""Opt-in LRU cache for AI documentation generation."""

from __future__ import annotations

import hashlib
import json
import os
from collections import OrderedDict
from typing import Any

_DOC_CACHE: OrderedDict[str, Any] = OrderedDict()
_DOC_CACHE_MAX = 32


def cache_clear() -> None:
    """Clear the documentation generation cache (primarily for tests)."""
    _DOC_CACHE.clear()


def get_cached(key: str) -> Any | None:
    if key in _DOC_CACHE:
        _DOC_CACHE.move_to_end(key)
        return _DOC_CACHE[key]
    return None


def set_cached(key: str, value: Any) -> None:
    _DOC_CACHE[key] = value
    _DOC_CACHE.move_to_end(key)
    while len(_DOC_CACHE) > _DOC_CACHE_MAX:
        _DOC_CACHE.popitem(last=False)


def make_doc_cache_key(iterable: Any, params: dict[str, Any], sample_size: int) -> str:
    """Build a stable cache key from iterable identity and generation parameters."""
    if isinstance(iterable, str) and os.path.exists(iterable):
        stat = os.stat(iterable)
        iterable_part = f"path:{iterable}:{stat.st_mtime_ns}:{stat.st_size}"
    else:
        try:
            if isinstance(iterable, str):
                from ..helpers.detect import open_iterable

                rows = []
                with open_iterable(iterable) as source:
                    for i, row in enumerate(source):
                        if i >= sample_size:
                            break
                        rows.append(row)
            else:
                rows = []
                for i, row in enumerate(iterable):
                    if i >= sample_size:
                        break
                    rows.append(row)
            digest = hashlib.sha256(json.dumps(rows, default=str, sort_keys=True).encode()).hexdigest()
            iterable_part = f"iter:{digest}"
        except Exception:
            iterable_part = f"iter:{hashlib.sha256(repr(iterable).encode()).hexdigest()}"

    param_blob = json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha256(f"{iterable_part}|{param_blob}".encode()).hexdigest()
