"""Apache Paimon table support via ``pypaimon``."""

from __future__ import annotations

import typing
from typing import Any

try:
    from pypaimon import CatalogFactory, Schema

    HAS_PYPAIMON = True
except ImportError:
    HAS_PYPAIMON = False

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError
from ..helpers.lakehouse_write import infer_arrow_schema, records_to_arrow_table
from ..types import Row

DEFAULT_BATCH_SIZE = 1024


def _require_pypaimon() -> None:
    if not HAS_PYPAIMON:
        raise ImportError(
            "Paimon table support requires the 'pypaimon' package. "
            "Install with: pip install iterabledata[paimon-table]"
        )


class PaimonTableIterable(BaseFileIterable):
    """Apache Paimon catalog table reader/writer.

    Distinct from standalone ``paimon_row`` / ``paimon_mosaic`` file formats.
    Memory behavior: prefers ``to_arrow_batch_reader`` / ``to_iterator`` over
    full-table materialization.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        mode: str = "r",
        codec: BaseCodec | None = None,
        database: str | None = None,
        table: str | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        columns: list[str] | None = None,
        create_table: bool = False,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        else:
            options = dict(options)
        if stream is not None:
            raise ReadError(
                "Paimon tables require a warehouse path, not a stream",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        _require_pypaimon()
        self.batch_size = int(options.pop("batch_size", batch_size))
        self.database = options.pop("database", database) or "default"
        self.table_name = options.pop("table", options.pop("table_name", table))
        self.columns = options.pop("columns", columns)
        self._create_table = bool(options.pop("create_table", create_table))
        self._catalog_options = dict(options.pop("catalog_options", {}) or {})
        self._buffer: list[Row] = []
        self._arrow_schema = options.pop("schema", None)
        self._catalog: Any | None = None
        self._table: Any | None = None
        self._iterator: typing.Iterator[dict[str, Any]] | None = None
        self.pos = 0
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, noopen=True, options=options)
        if self.filename is None:
            raise ReadError(
                "Paimon tables require a warehouse path (filename)",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        if self.table_name is None and mode == "r":
            raise ReadError(
                "Paimon tables require iterableargs={'database': '...', 'table': '...'}",
                filename=self.filename,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        self.reset()

    def _table_id(self) -> str:
        name = str(self.table_name)
        if "." in name:
            return name
        return f"{self.database}.{name}"

    def _open_catalog(self) -> Any:
        opts = {"warehouse": self.filename, **self._catalog_options}
        return CatalogFactory.create(opts)

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        self._iterator = None
        self._catalog = self._open_catalog()
        self._table = None
        if self.mode == "r":
            if self.table_name is None:
                raise ReadError(
                    "Paimon tables require iterableargs={'database': '...', 'table': '...'}",
                    filename=self.filename,
                    error_code="RESOURCE_REQUIREMENT_NOT_MET",
                )
            self._table = self._catalog.get_table(self._table_id())
            self._iterator = self._iter_rows()
        else:
            self._buffer = []
            if self.table_name is None:
                self.table_name = "data"
            try:
                self._table = self._catalog.get_table(self._table_id())
            except Exception:
                if not self._create_table:
                    raise ReadError(
                        f"Paimon table '{self._table_id()}' not found; pass create_table=True to create it",
                        filename=self.filename,
                        error_code="RESOURCE_REQUIREMENT_NOT_MET",
                    ) from None
                self._table = None

    def _iter_rows(self) -> typing.Iterator[dict[str, Any]]:
        assert self._table is not None
        read_builder = self._table.new_read_builder()
        if self.columns and hasattr(read_builder, "with_projection"):
            read_builder = read_builder.with_projection(list(self.columns))
        splits = read_builder.new_scan().plan().splits()
        reader = read_builder.new_read()
        if hasattr(reader, "to_arrow_batch_reader"):
            for batch in reader.to_arrow_batch_reader(splits):
                yield from batch.to_pylist()
            return
        if hasattr(reader, "to_arrow"):
            yield from reader.to_arrow(splits).to_pylist()
            return
        # Iterator path: copy fields because OffsetRow may be reused.
        field_names = [f.name for f in self._table.schema.fields] if hasattr(self._table, "schema") else None
        if field_names is None and self.columns:
            field_names = list(self.columns)
        for row in reader.to_iterator(splits):
            if field_names is None:
                arity = len(row) if hasattr(row, "__len__") else 0
                field_names = [f"f{i}" for i in range(arity)]
            yield {name: row.get_field(i) for i, name in enumerate(field_names)}

    @staticmethod
    def id() -> str:
        return "paimon"

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
        path = filename if filename is not None else self.filename
        if path is None:
            return None
        _require_pypaimon()
        catalog = CatalogFactory.create({"warehouse": path, **self._catalog_options})
        out: list[str] = []
        for database in catalog.list_databases():
            for table in catalog.list_tables(database):
                out.append(f"{database}.{table}")
        return sorted(out)

    def totals(self) -> int:
        if self.mode != "r" or self._table is None:
            return 0
        read_builder = self._table.new_read_builder()
        splits = read_builder.new_scan().plan().splits()
        reader = read_builder.new_read()
        if hasattr(reader, "to_arrow_batch_reader"):
            return sum(batch.num_rows for batch in reader.to_arrow_batch_reader(splits))
        if hasattr(reader, "to_arrow"):
            return len(reader.to_arrow(splits))
        return sum(1 for _ in reader.to_iterator(splits))

    def read(self, skip_empty: bool = True) -> dict:
        if self._iterator is None:
            raise RuntimeError("Iterator not initialized. Call reset() first.")
        row = next(self._iterator)
        self.pos += 1
        return row

    def _ensure_table_for_write(self, records: list[Row]) -> None:
        if self._table is not None:
            return
        assert self._catalog is not None
        if self._arrow_schema is None:
            self._arrow_schema = infer_arrow_schema(records)
        # Ensure database exists
        try:
            self._catalog.create_database(self.database, True)
        except TypeError:
            self._catalog.create_database(self.database, ignore_if_exists=True)
        schema = Schema.from_pyarrow_schema(self._arrow_schema)
        table_id = self._table_id()
        try:
            self._catalog.create_table(table_id, schema, True)
        except TypeError:
            self._catalog.create_table(table_id, schema, ignore_if_exists=True)
        self._table = self._catalog.get_table(table_id)

    def _flush_buffer(self) -> None:
        if not self._buffer:
            return
        self._ensure_table_for_write(self._buffer)
        assert self._table is not None
        table = records_to_arrow_table(self._buffer, schema=self._arrow_schema)
        if self._arrow_schema is None:
            self._arrow_schema = table.schema
        write_builder = self._table.new_batch_write_builder()
        writer = write_builder.new_write()
        commit = write_builder.new_commit()
        try:
            writer.write_arrow(table)
            commit.commit(writer.prepare_commit())
        finally:
            writer.close()
            commit.close()
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
        super().close()
