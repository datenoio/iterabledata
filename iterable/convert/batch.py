"""Optional native batch conversion protocol.

The protocol is deliberately small: row-oriented formats continue to use the
existing ``read_bulk``/``write_bulk`` fallback, while columnar backends can
advertise a batch path without making it mandatory for every datatype.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

PREDICATE_OPERATORS = ("==", "!=", "<", "<=", ">", ">=")

_COMPARATORS = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
}


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


def _is_comparison(value: Any) -> bool:
    """Return whether ``value`` looks like a (field, op, literal) triple."""
    return (
        isinstance(value, (tuple, list))
        and len(value) == 3
        and isinstance(value[0], str)
        and value[1] in PREDICATE_OPERATORS
    )


def normalize_predicate(predicate: Any) -> tuple[tuple[str, str, Any], ...] | None:
    """Normalize a structured predicate to AND-ed (field, op, literal) triples.

    Structured predicates are the portable representation shared by every
    backend adapter: a single ``(field, op, value)`` comparison or a
    sequence of comparisons combined with logical AND.

    Raw backend-native expressions (``pyarrow.compute.Expression``,
    ``pyiceberg`` boolean expressions, SQL filter strings) are trusted APIs
    handled by the concrete backend and raise :exc:`NotImplementedError`
    here because they cannot be evaluated portably row by row.
    """
    if predicate is None:
        return None
    if _is_comparison(predicate):
        return ((predicate[0], predicate[1], predicate[2]),)
    if isinstance(predicate, (tuple, list)) and predicate and all(_is_comparison(item) for item in predicate):
        return tuple((item[0], item[1], item[2]) for item in predicate)
    raise NotImplementedError(
        "Unsupported predicate form. Use structured (field, op, value) comparisons "
        f"(op one of {PREDICATE_OPERATORS}) or a backend-native expression accepted "
        "by the source adapter."
    )


def row_matches_predicate(row: Mapping[str, Any], predicate: Any) -> bool:
    """Evaluate a structured predicate against a single row.

    Rows whose compared field is ``None`` never match (SQL-like semantics:
    NULL comparisons are not true).
    """
    comparisons = normalize_predicate(predicate)
    if comparisons is None:
        return True
    for field, op, value in comparisons:
        current = row.get(field)
        if current is None:
            return False
        try:
            if not _COMPARATORS[op](current, value):
                return False
        except TypeError:
            return False
    return True


def to_pyarrow_expression(predicate: Any) -> Any:
    """Translate a structured predicate into a ``pyarrow.compute`` expression.

    ``pyarrow.compute.Expression`` instances pass through unchanged (trusted
    raw API). PyArrow is imported lazily so core code never depends on it.
    """
    if predicate is None:
        return None
    import pyarrow.compute as pc

    if isinstance(predicate, pc.Expression):
        return predicate
    comparisons = normalize_predicate(predicate)
    ops = {
        "==": pc.equal,
        "!=": pc.not_equal,
        "<": pc.less,
        "<=": pc.less_equal,
        ">": pc.greater,
        ">=": pc.greater_equal,
    }
    expression = None
    for field, op, value in comparisons or ():
        term = ops[op](pc.field(field), value)
        expression = term if expression is None else (expression & term)
    return expression


def resolve_row_window(selection: BatchSelection) -> tuple[int, int | None, int]:
    """Resolve row_range/slice into a (start, stop, step) row window.

    The window applies after any predicate filtering, matching backend
    offset/limit semantics (e.g. Lance scanner ``offset``/``limit``).
    """
    start, stop, step = 0, None, 1
    if selection.row_range is not None:
        start, stop = selection.row_range
    if selection.slice is not None:
        slice_start, slice_stop, slice_step = selection.slice
        start = slice_start
        stop = slice_stop
        step = slice_step or 1
    if start < 0:
        raise NotImplementedError("Negative row selection starts are not supported")
    if step <= 0:
        raise NotImplementedError("Row selection step must be a positive integer")
    return start, stop, step


def select_rows(rows: Iterable[Mapping[str, Any]], selection: BatchSelection) -> Iterable[dict[str, Any]]:
    """Apply predicate, row window, and projection to a row stream.

    This is the documented row-level fallback used when a backend cannot
    push part of a selection down; results match the pushed-down path.
    """
    comparisons = normalize_predicate(selection.predicate)
    start, stop, step = resolve_row_window(selection)
    columns = selection.columns
    matched = 0
    for row in rows:
        if comparisons is not None and not row_matches_predicate(row, comparisons):
            continue
        if matched < start:
            matched += 1
            continue
        if stop is not None and matched >= stop:
            break
        if (matched - start) % step != 0:
            matched += 1
            continue
        matched += 1
        if columns is not None:
            yield {name: row.get(name) for name in columns}
        elif isinstance(row, dict):
            # Fast path: source rows are already fresh dicts; avoid a copy.
            yield row
        else:
            yield dict(row)


def chunk_rows(rows: Iterable[dict[str, Any]], batch_size: int) -> Iterable[list[dict[str, Any]]]:
    """Re-chunk a row stream into list-of-dict batches."""
    chunk: list[dict[str, Any]] = []
    for row in rows:
        chunk.append(row)
        if len(chunk) >= batch_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def _sql_literal(value: Any) -> str:
    """Render a Python literal for a SQL filter string (Lance/DataFusion)."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    raise NotImplementedError(f"Unsupported SQL filter literal: {value!r}")


def to_sql_filter(predicate: Any) -> str | None:
    """Translate a structured predicate into a SQL WHERE clause body.

    Plain strings pass through unchanged as a trusted raw filter expression.
    """
    if predicate is None:
        return None
    if isinstance(predicate, str):
        return predicate
    comparisons = normalize_predicate(predicate)
    clauses = []
    for field, op, value in comparisons or ():
        quoted = '"' + field.replace('"', '""') + '"'
        if value is None:
            if op == "==":
                clauses.append(f"{quoted} IS NULL")
                continue
            if op == "!=":
                clauses.append(f"{quoted} IS NOT NULL")
                continue
        clauses.append(f"{quoted} {op} {_sql_literal(value)}")
    return " AND ".join(clauses)
