"""Skip helpers for optional datatype/codec classes that are unbound without extras."""

from __future__ import annotations

from typing import Any

import pytest

import iterable.codecs as codecs
import iterable.datatypes as datatypes


def require_datatype(name: str) -> Any:
    """Return an optional datatype class, or skip the module if extras are missing."""
    cls = getattr(datatypes, name, None)
    if cls is None:
        pytest.skip(
            f"{name} requires an optional extra that is not installed",
            allow_module_level=True,
        )
    return cls


def require_codec(name: str) -> Any:
    """Return an optional codec class, or skip the module if extras are missing."""
    cls = getattr(codecs, name, None)
    if cls is None:
        pytest.skip(
            f"{name} requires an optional extra that is not installed",
            allow_module_level=True,
        )
    return cls
