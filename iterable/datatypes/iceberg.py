from __future__ import annotations

import os
import typing

try:
    import pyarrow as pa
    import pyiceberg  # noqa: F401
    from pyiceberg.catalog import load_catalog
    from pyiceberg.schema import Schema as IcebergSchema
    from pyiceberg.types import (
        BooleanType,
        DoubleType,
        FloatType,
        LongType,
        NestedField,
        StringType,
    )

    HAS_PYICEBERG = True
except ImportError:
    HAS_PYICEBERG = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..convert.batch import BatchSelection, chunk_rows, normalize_predicate, resolve_row_window, select_rows
from ..exceptions import ReadError, WriteNotSupportedError
from ..helpers.lakehouse_write import infer_arrow_schema, records_to_arrow_table
from ..types import Row

DEFAULT_BATCH_SIZE = 1024


def _arrow_to_iceberg_schema(arrow_schema: Any) -> Any:
    fields = []
    for idx, field in enumerate(arrow_schema, start=1):
        t = field.type
        if pa.types.is_boolean(t):
            ice_t = BooleanType()
        elif pa.types.is_floating(t) and pa.types.is_float32(t):
            ice_t = FloatType()
        elif pa.types.is_floating(t):
            ice_t = DoubleType()
        elif pa.types.is_integer(t):
            ice_t = LongType()
        else:
            ice_t = StringType()
        fields.append(NestedField(idx, field.name, ice_t, required=not field.nullable))
    return IcebergSchema(*fields)


def _to_iceberg_filter(predicate: Any) -> Any:
    """Translate a structured predicate into a PyIceberg row filter.

    Plain strings and PyIceberg boolean expressions pass through unchanged
    (trusted raw API). Other raw expressions raise
    :exc:`NotImplementedError` so the documented row fallback applies.
    """
    if predicate is None:
        return None
    from pyiceberg.expressions import (
        And,
        BooleanExpression,
        EqualTo,
        GreaterThan,
        GreaterThanOrEqual,
        LessThan,
        LessThanOrEqual,
        NotEqualTo,
    )

    if isinstance(predicate, (str, BooleanExpression)):
        return predicate
    comparisons = normalize_predicate(predicate)
    ops = {
        "==": EqualTo,
        "!=": NotEqualTo,
        "<": LessThan,
        "<=": LessThanOrEqual,
        ">": GreaterThan,
        ">=": GreaterThanOrEqual,
    }
    expression = None
    for field, op, value in comparisons or ():
        term = ops[op](field, value)
        expression = term if expression is None else And(expression, term)
    return expression


class IcebergIterable(BaseFileIterable):
    """Apache Iceberg table reader/writer.

    Memory behavior: records are read batch by batch via the scan's
    ``to_arrow_batch_reader()`` when available. Writes append Arrow tables
    through PyIceberg and flush at ``batch_size``.
    """

    datamode = "binary"
    supports_native_batch = False

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        catalog_name: str | None = None,
        table_name: str | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        create_table: bool = False,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        else:
            options = dict(options)
        if not HAS_PYICEBERG:
            raise ImportError(
                "Apache Iceberg support requires the 'pyiceberg' package. "
                "Install with: pip install iterabledata[lakehouse]"
            )
        self.batch_size = int(options.pop("batch_size", batch_size))
        self._create_table = bool(options.pop("create_table", create_table))
        self.catalog_name = options.pop("catalog_name", catalog_name)
        self.table_name = options.pop("table_name", options.pop("table", table_name))
        self.catalog_props = dict(options.pop("catalog", options.pop("catalog_properties", {}) or {}))
        self._buffer: list[Row] = []
        self._arrow_schema = options.pop("schema", None)
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, noopen=True, options=options)
        if "catalog_name" in options:
            self.catalog_name = options["catalog_name"]
        if "table_name" in options:
            self.table_name = options["table_name"]
        if stream is not None:
            raise ReadError(
                "Iceberg requires catalog and table names, not a stream",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        if self.catalog_name is None:
            self.catalog_name = "default"
        if self.table_name is None:
            raise ReadError(
                "Iceberg requires table_name parameter",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        self.table = None
        self.scan_result = None
        self.iterator = None
        self._catalog = None
        # Native batches (scan projection/filter pushdown) are available
        # whenever the pyiceberg backend is importable.
        self.supports_native_batch = HAS_PYICEBERG
        self.reset()

    def _load_catalog(self):
        props = dict(self.catalog_props)
        if self.filename and os.path.exists(self.filename) and not props:
            return load_catalog(self.catalog_name, **{"properties": self.filename})
        if props:
            return load_catalog(self.catalog_name, **props)
        return load_catalog(self.catalog_name)

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        self._catalog = self._load_catalog()
        self.table = None
        self.scan_result = None
        self.iterator = None
        if self.mode == "r":
            self.table = self._catalog.load_table(self.table_name)
            self.scan_result = self.table.scan()
            self.iterator = self.__iterator(self.scan_result)
        else:
            self._buffer = []
            try:
                self.table = self._catalog.load_table(self.table_name)
            except Exception:
                if not self._create_table:
                    raise ReadError(
                        f"Iceberg table '{self.table_name}' not found; pass create_table=True to create it",
                        filename=self.filename,
                        error_code="RESOURCE_REQUIREMENT_NOT_MET",
                    ) from None
                self.table = None

    @staticmethod
    def __iterator(scan):
        if hasattr(scan, "to_arrow_batch_reader"):
            for batch in scan.to_arrow_batch_reader():
                yield from batch.to_pylist()
        else:
            yield from scan.to_arrow().to_pylist()

    @staticmethod
    def has_totals() -> bool:
        return True

    def totals(self):
        if self.table is None:
            return 0
        scan = self.table.scan()
        if hasattr(scan, "to_arrow_batch_reader"):
            return sum(batch.num_rows for batch in scan.to_arrow_batch_reader())
        return len(scan.to_arrow())

    @staticmethod
    def id() -> str:
        return "iceberg"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return hasattr(self.scan_result, "to_arrow_batch_reader")

    @staticmethod
    def has_tables() -> bool:
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        if not HAS_PYICEBERG:
            return None
        catalog_name = self.catalog_name if hasattr(self, "catalog_name") else None
        if catalog_name is None:
            return None
        try:
            if filename and os.path.exists(filename) and not self.catalog_props:
                catalog = load_catalog(catalog_name, **{"properties": filename})
            elif self.catalog_props:
                catalog = load_catalog(catalog_name, **self.catalog_props)
            elif hasattr(self, "filename") and self.filename and os.path.exists(self.filename):
                catalog = load_catalog(catalog_name, **{"properties": self.filename})
            else:
                catalog = load_catalog(catalog_name)
            if hasattr(catalog, "list_tables") and hasattr(catalog, "list_namespaces"):
                all_tables = []
                for ns in catalog.list_namespaces():
                    try:
                        tables = catalog.list_tables(ns)
                        all_tables.extend([str(t) for t in tables])
                    except Exception:
                        continue
                return sorted(all_tables) if all_tables else []
            if hasattr(catalog, "list_tables"):
                tables = catalog.list_tables()
                return [str(t) for t in tables] if tables else []
            return []
        except Exception:
            return None

    def read(self, skip_empty: bool = True) -> dict:
        try:
            row = next(self.iterator)
            self.pos += 1
            return row
        except (StopIteration, EOFError, ValueError):
            raise StopIteration from None

    def read_batches(self, selection: BatchSelection | None = None):
        """Yield Iceberg scan batches with projection/filter pushdown.

        Column projection maps to ``selected_fields`` and structured
        predicates to PyIceberg row filters (requires ``pyiceberg>=0.5``).
        A limit is pushed when the window starts at zero with no step;
        remaining offset/step semantics are applied after the scan,
        identical to the row fallback.
        """
        selection = selection or BatchSelection()
        if selection.table is not None:
            raise NotImplementedError("Iceberg native batches do not support table selection")
        if self.table is None:
            return
        start, stop, step = resolve_row_window(selection)
        target = selection.batch_size or self.batch_size
        scan_kwargs: dict[str, Any] = {}
        if selection.columns is not None:
            scan_kwargs["selected_fields"] = tuple(selection.columns)
        if selection.predicate is not None:
            scan_kwargs["row_filter"] = _to_iceberg_filter(selection.predicate)
        if start == 0 and step == 1 and stop is not None:
            scan_kwargs["limit"] = stop
        scan = self.table.scan(**scan_kwargs)

        def rows():
            if hasattr(scan, "to_arrow_batch_reader"):
                for batch in scan.to_arrow_batch_reader():
                    yield from batch.to_pylist()
            else:
                yield from scan.to_arrow().to_pylist()

        window = BatchSelection(row_range=(start, stop) if start or stop is not None else None)
        if step != 1:
            window = BatchSelection(slice=(start, stop, step))

        for chunk in chunk_rows(select_rows(rows(), window), target):
            self.pos += len(chunk)
            yield chunk

    def write_batch(self, records: list[Row]) -> None:
        """Native batch writer hook used by columnar conversion."""
        self.write_bulk(records)

    def _ensure_table_for_write(self, records: list[Row]) -> None:
        if self.table is not None:
            return
        assert self._catalog is not None
        if self._arrow_schema is None:
            self._arrow_schema = infer_arrow_schema(records)
        ice_schema = _arrow_to_iceberg_schema(self._arrow_schema)
        # namespace from table_name "ns.table"
        if "." in str(self.table_name):
            ns = str(self.table_name).split(".", 1)[0]
            try:
                self._catalog.create_namespace(ns)
            except Exception:
                pass
        self.table = self._catalog.create_table(self.table_name, schema=ice_schema)

    def _flush_buffer(self) -> None:
        if not self._buffer:
            return
        self._ensure_table_for_write(self._buffer)
        assert self.table is not None
        table = records_to_arrow_table(self._buffer, schema=self._arrow_schema)
        if self._arrow_schema is None:
            self._arrow_schema = table.schema
        self.table.append(table)
        self._buffer = []

    def write(self, record: Row) -> None:
        self.write_bulk([record])

    def write_bulk(self, records: list[Row]) -> None:
        if self.mode != "w":
            raise WriteNotSupportedError("iceberg", "Iceberg is open read-only")
        if not records:
            return
        self._buffer.extend(records)
        if len(self._buffer) >= self.batch_size:
            self._flush_buffer()

    def flush(self) -> None:
        if self.mode == "w":
            self._flush_buffer()

    def close(self) -> None:
        if self.mode == "w":
            self._flush_buffer()
        super().close()
