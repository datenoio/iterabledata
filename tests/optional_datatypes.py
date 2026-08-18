"""Skip helpers for optional datatype classes that are unbound without extras."""

from __future__ import annotations

from typing import Any

import pytest

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
