"""DuckLake table format support via ``pyducklake``."""

from __future__ import annotations

import typing
from typing import Any

try:
    import pyarrow as pa
    from pyducklake import (
        BigIntType,
        BooleanType,
        Catalog,
        DoubleType,
        FloatType,
        IntegerType,
        Schema,
        StringType,
        optional,
        required,
    )

    HAS_PYDUCKLAKE = True
except ImportError:
    HAS_PYDUCKLAKE = False

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError
from ..helpers.lakehouse_write import infer_arrow_schema, records_to_arrow_table
from ..types import Row

DEFAULT_BATCH_SIZE = 1024


def _require_ducklake() -> None:
    if not HAS_PYDUCKLAKE:
        raise ImportError(
            "DuckLake support requires the 'pyducklake' package. Install with: pip install iterabledata[ducklake]"
        )


def _arrow_field_to_ducklake(field: Any) -> Any:
    t = field.type
    if pa.types.is_boolean(t):
        dl_type = BooleanType()
    elif pa.types.is_int8(t) or pa.types.is_int16(t) or pa.types.is_int32(t):
        dl_type = IntegerType()
    elif pa.types.is_integer(t):
        dl_type = BigIntType()
    elif pa.types.is_float32(t):
        dl_type = FloatType()
    elif pa.types.is_floating(t):
        dl_type = DoubleType()
    else:
        dl_type = StringType()
    return required(field.name, dl_type) if not field.nullable else optional(field.name, dl_type)


def _schema_from_arrow(arrow_schema: Any) -> Any:
    return Schema.of(*[_arrow_field_to_ducklake(field) for field in arrow_schema])


def _format_table_id(item: Any) -> str:
    if isinstance(item, tuple) and len(item) == 2:
        return f"{item[0]}.{item[1]}"
    return str(item)


class DuckLakeIterable(BaseFileIterable):
    """DuckLake catalog table reader/writer.

    Memory behavior: reads stream Arrow record batches via
    ``table.scan().to_arrow_batch_reader()``; writes flush at ``batch_size``.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        mode: str = "r",
        codec: BaseCodec | None = None,
        table: str | None = None,
        data_path: str | None = None,
        catalog_name: str = "lake",
        batch_size: int = DEFAULT_BATCH_SIZE,
        write_mode: str = "append",
        create_table: bool = False,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        else:
            options = dict(options)
        if stream is not None:
            raise ReadError(
                "DuckLake requires a catalog path/URI, not a stream",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        _require_ducklake()
        self.batch_size = int(options.pop("batch_size", batch_size))
        self.write_mode = str(options.pop("write_mode", write_mode)).lower()
        self.catalog_name = options.pop("catalog_name", catalog_name)
        self.data_path = options.pop("data_path", data_path)
        self.table_name = options.pop("table", options.pop("table_name", table))
        if self.table_name is not None:
            self.table_name = str(self.table_name)
        self._create_table = bool(options.pop("create_table", create_table))
        self._buffer: list[Row] = []
        self._arrow_schema = options.pop("schema", None)
        self._catalog: Any | None = None
        self._table: Any | None = None
        self._iterator: typing.Iterator[dict[str, Any]] | None = None
        self.pos = 0
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, noopen=True, options=options)
        if self.filename is None:
            raise ReadError(
                "DuckLake requires a catalog metadata path (e.g. meta.duckdb)",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        self.reset()

    def _open_catalog(self) -> Any:
        kwargs: dict[str, Any] = {}
        if self.data_path is not None:
            kwargs["data_path"] = self.data_path
        return Catalog(self.catalog_name, self.filename, **kwargs)

    def _listed_tables(self, catalog: Any) -> list[str]:
        return sorted(_format_table_id(item) for item in catalog.list_tables())

    def _resolve_table_name(self, available: list[str]) -> str:
        if self.table_name is None:
            if len(available) == 1:
                return available[0]
            if not available:
                raise ReadError(
                    "DuckLake catalog has no tables; provide table= (and create_table=True when writing)",
                    filename=self.filename,
                    error_code="RESOURCE_REQUIREMENT_NOT_MET",
                )
            raise ReadError(
                "DuckLake catalog has multiple tables; set iterableargs={'table': 'ns.name'}. "
                f"Available: {', '.join(available)}",
                filename=self.filename,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        name = self.table_name
        if name in available:
            return name
        if "." not in name:
            matches = [t for t in available if t == name or t.endswith("." + name)]
            if len(matches) == 1:
                return matches[0]
            candidate = f"main.{name}"
            if candidate in available:
                return candidate
            if self.mode == "w" and self._create_table:
                return candidate
        if self.mode == "w" and self._create_table:
            return name if "." in name else f"main.{name}"
        raise ReadError(
            f"DuckLake table '{self.table_name}' not found. Available: {', '.join(available) or '(none)'}",
            filename=self.filename,
            error_code="RESOURCE_REQUIREMENT_NOT_MET",
        )

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        self._iterator = None
        if self._catalog is not None:
            try:
                self._catalog.close()
            except Exception:
                pass
            self._catalog = None
        self._table = None
        self._catalog = self._open_catalog()
        available = self._listed_tables(self._catalog)
        self.table_name = self._resolve_table_name(available)
        if self.mode == "r":
            self._table = self._catalog.load_table(self.table_name)
            self._iterator = self._iter_rows()
        else:
            if self.write_mode not in {"append", "overwrite", "error", "create"}:
                raise ValueError(f"Unsupported DuckLake write_mode: {self.write_mode}")
            self._buffer = []
            if self.table_name in available:
                self._table = self._catalog.load_table(self.table_name)
            elif not self._create_table:
                raise ReadError(
                    f"DuckLake table '{self.table_name}' not found; pass create_table=True to create it",
                    filename=self.filename,
                    error_code="RESOURCE_REQUIREMENT_NOT_MET",
                )

    def _iter_rows(self) -> typing.Iterator[dict[str, Any]]:
        assert self._table is not None
        scan = self._table.scan()
        if hasattr(scan, "to_arrow_batch_reader"):
            for batch in scan.to_arrow_batch_reader():
                yield from batch.to_pylist()
        else:
            yield from scan.to_arrow().to_pylist()

    @staticmethod
    def id() -> str:
        return "ducklake"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    @staticmethod
    def has_totals() -> bool:
        return True

    @staticmethod
    def has_tables() -> bool:
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        if filename is None and self._catalog is not None:
            return self._listed_tables(self._catalog)
        path = filename if filename is not None else self.filename
        if path is None:
            return None
        _require_ducklake()
        kwargs: dict[str, Any] = {}
        if self.data_path is not None:
            kwargs["data_path"] = self.data_path
        catalog = Catalog(self.catalog_name, path, **kwargs)
        try:
            return self._listed_tables(catalog)
        finally:
            try:
                catalog.close()
            except Exception:
                pass

    def totals(self) -> int:
        if self.mode != "r" or self._table is None:
            return 0
        scan = self._table.scan()
        if hasattr(scan, "count"):
            return int(scan.count())
        if hasattr(scan, "to_arrow_batch_reader"):
            return sum(batch.num_rows for batch in scan.to_arrow_batch_reader())
        return len(scan.to_arrow())

    def read(self, skip_empty: bool = True) -> dict:
        if self._iterator is None:
            raise RuntimeError("Iterator not initialized. Call reset() first.")
        row = next(self._iterator)
        self.pos += 1
        return row

    def _ensure_table_for_write(self, records: list[Row]) -> None:
        if self._table is not None:
            return
        assert self._catalog is not None and self.table_name is not None
        if self._arrow_schema is None:
            self._arrow_schema = infer_arrow_schema(records)
        schema = _schema_from_arrow(self._arrow_schema)
        self._table = self._catalog.create_table(self.table_name, schema)

    def _flush_buffer(self) -> None:
        if not self._buffer:
            return
        self._ensure_table_for_write(self._buffer)
        assert self._table is not None
        table = records_to_arrow_table(self._buffer, schema=self._arrow_schema)
        if self._arrow_schema is None:
            self._arrow_schema = table.schema
        mode = "append" if self.write_mode in {"append", "create"} else self.write_mode
        if mode == "error":
            existing = 0
            try:
                scan = self._table.scan()
                existing = int(scan.count()) if hasattr(scan, "count") else len(scan.to_arrow())
            except Exception:
                existing = 0
            if existing > 0:
                raise ValueError("DuckLake write_mode=error but table already has rows")
            mode = "append"
        if mode == "overwrite" and hasattr(self._table, "overwrite"):
            self._table.overwrite(table)
        else:
            self._table.append(table)
        self._buffer = []

    def write(self, record: Row) -> None:
        self.write_bulk([record])

    def write_bulk(self, records: list[Row]) -> None:
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
        if self._catalog is not None:
            try:
                self._catalog.close()
            except Exception:
                pass
            self._catalog = None
        super().close()
