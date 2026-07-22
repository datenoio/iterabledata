"""Shared helpers for lakehouse table writers (Delta / Iceberg / etc.)."""

from __future__ import annotations

from typing import Any

from ..types import Row

try:
    import pyarrow as pa

    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False


def require_pyarrow() -> None:
    if not HAS_PYARROW:
        raise ImportError("Lakehouse writes require 'pyarrow'. Install with: pip install pyarrow")


def records_to_arrow_table(records: list[Row], schema: Any | None = None) -> Any:
    """Convert dictionary rows to a PyArrow Table."""
    require_pyarrow()
    if not records:
        if schema is not None:
            return pa.Table.from_pylist([], schema=schema)
        return pa.table({})
    if schema is not None:
        return pa.Table.from_pylist(records, schema=schema)
    return pa.Table.from_pylist(records)


def infer_arrow_schema(records: list[Row]) -> Any:
    """Infer a PyArrow schema from the first non-empty record batch."""
    require_pyarrow()
    if not records:
        raise ValueError("Cannot infer schema from an empty record list")
    return pa.Table.from_pylist(records).schema
