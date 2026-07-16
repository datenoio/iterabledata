"""Optional native batch conversion protocol.

The protocol is deliberately small: row-oriented formats continue to use the
existing ``read_bulk``/``write_bulk`` fallback, while columnar backends can
advertise a batch path without making it mandatory for every datatype.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class BatchSelection:
    """Optional operations that a backend may push down to its scanner."""

    columns: tuple[str, ...] | None = None
    predicate: Any = None
    table: str | None = None
    row_range: tuple[int, int] | None = None
    slice: tuple[int, int, int | None] | None = None
    batch_size: int | None = None

    @classmethod
    def from_value(cls, value: BatchSelection | Mapping[str, Any] | None) -> BatchSelection:
        if value is None:
            return cls()
        if isinstance(value, cls):
            return value
        values = dict(value)
        columns = values.get("columns")
        return cls(
            columns=tuple(columns) if columns is not None else None,
            predicate=values.get("predicate"),
            table=values.get("table"),
            row_range=tuple(values["row_range"]) if values.get("row_range") is not None else None,
            slice=tuple(values["slice"]) if values.get("slice") is not None else None,
            batch_size=values.get("batch_size"),
        )


@runtime_checkable
class NativeBatchReader(Protocol):
    """Optional reader protocol implemented by columnar datatypes."""

    supports_native_batch: bool

    def read_batches(self, selection: BatchSelection | None = None) -> Iterable[list[dict[str, Any]]]: ...


@runtime_checkable
class NativeBatchWriter(Protocol):
    """Optional writer protocol implemented by columnar datatypes."""

    supports_native_batch: bool

    def write_batch(self, records: list[dict[str, Any]]) -> None: ...


def native_batch_supported(reader: Any, writer: Any) -> bool:
    """Return whether both endpoints explicitly opt into native batches."""
    return bool(
        getattr(reader, "supports_native_batch", False)
        and getattr(writer, "supports_native_batch", False)
        and callable(getattr(reader, "read_batches", None))
        and callable(getattr(writer, "write_batch", None))
    )
