"""Microsoft Access ``.mdb`` / ``.accdb`` table reader.

Prefers the pure-Python ``access_parser`` package when available; falls back to
``pyodbc`` with a Jet/ACE connection string for ``.mdb`` files. Read-only.

Install with::

    pip install iterabledata[access]
"""

from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteNotSupportedError
from ..types import Row

try:
    import access_parser  # type: ignore[import-untyped]

    HAS_ACCESS_PARSER = True
except ImportError:
    HAS_ACCESS_PARSER = False

try:
    import pyodbc  # type: ignore[import-untyped]

    HAS_PYODBC = True
except ImportError:
    HAS_PYODBC = False


_ACCESS_IMPORT_ERROR = (
    "Microsoft Access (.mdb/.accdb) support requires 'access_parser' or 'pyodbc'. "
    "Install with: pip install iterabledata[access]"
)


def _require_backend() -> None:
    if not HAS_ACCESS_PARSER and not HAS_PYODBC:
        raise ImportError(_ACCESS_IMPORT_ERROR)


class AccessMDBIterable(BaseFileIterable):
    """Read-only Microsoft Access database iterable (``id`` = ``mdb``)."""

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        table: str | None = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if mode not in ("r", "rb"):
            raise WriteNotSupportedError("mdb", "Access MDB is read-only")
        _require_backend()
        if stream is not None or codec is not None:
            raise ReadError(
                "Access MDB reading requires a filename, not a stream or codec",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        if filename is None:
            raise ReadError(
                "Access MDB reading requires a filename",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        self.table = table if table is not None else options.pop("table", None)
        super().__init__(
            filename=filename,
            stream=None,
            codec=None,
            binary=True,
            mode="r",
            noopen=True,
            options=options,
        )
        self._db: Any = None
        self._conn: Any = None
        self._rows: list[dict[str, Any]] = []
        self._iterator: typing.Iterator[dict[str, Any]] | None = None
        self.reset()

    @staticmethod
    def id() -> str:
        return "mdb"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_tables() -> bool:
        return True

    def is_streaming(self) -> bool:
        return False

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        target = filename if filename is not None else self.filename
        if target is None:
            return None
        return self._list_tables_for(target)

    @classmethod
    def _list_tables_for(cls, path: str) -> list[str]:
        _require_backend()
        if HAS_ACCESS_PARSER:
            db = access_parser.AccessParser(path)
            tables = getattr(db, "catalog", None) or getattr(db, "tables", None)
            if isinstance(tables, dict):
                return sorted(tables.keys())
            if callable(getattr(db, "parse_table", None)):
                # access_parser exposes .catalog as dict of table -> columns
                catalog = getattr(db, "catalog", {})
                return sorted(catalog.keys()) if catalog else []
            return []
        assert HAS_PYODBC
        conn = pyodbc.connect(cls._odbc_conn_str(path))
        try:
            cursor = conn.cursor()
            names = [row.table_name for row in cursor.tables(tableType="TABLE")]
            return sorted(names)
        finally:
            conn.close()

    @staticmethod
    def _odbc_conn_str(path: str) -> str:
        # Prefer ACE, fall back to Jet for classic .mdb.
        return r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + path + ";"

    def reset(self) -> None:
        self.pos = 0
        assert self.filename is not None
        tables = self._list_tables_for(self.filename)
        if not tables:
            raise ReadError(
                f"No user tables found in Access database: {self.filename}",
                filename=self.filename,
                error_code="EMPTY_SOURCE",
            )
        if self.table is None:
            if len(tables) == 1:
                self.table = tables[0]
            else:
                raise ReadError(
                    f"Multiple tables found ({tables}); specify table= explicitly",
                    filename=self.filename,
                    error_code="TABLE_REQUIRED",
                )
        elif self.table not in tables:
            raise ReadError(
                f"Table {self.table!r} not found; available: {tables}",
                filename=self.filename,
                error_code="TABLE_NOT_FOUND",
            )

        self._rows = self._read_table(self.filename, self.table)
        self._iterator = iter(self._rows)

    def _read_table(self, path: str, table: str) -> list[dict[str, Any]]:
        if HAS_ACCESS_PARSER:
            db = access_parser.AccessParser(path)
            raw = db.parse_table(table)
            # access_parser returns dict of column -> list of values
            if isinstance(raw, dict) and raw:
                columns = list(raw.keys())
                length = len(next(iter(raw.values())))
                rows: list[dict[str, Any]] = []
                for i in range(length):
                    rows.append({col: raw[col][i] for col in columns})
                return rows
            if isinstance(raw, list):
                return [dict(r) if not isinstance(r, dict) else r for r in raw]
            return []

        assert HAS_PYODBC
        conn = pyodbc.connect(self._odbc_conn_str(path))
        try:
            cursor = conn.cursor()
            # Bracket table name for Access SQL safety on reserved words.
            cursor.execute(f"SELECT * FROM [{table}]")
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]
        finally:
            conn.close()

    def read(self, skip_empty: bool = True) -> Row:
        if self._iterator is None:
            raise StopIteration
        row = next(self._iterator)
        self.pos += 1
        return row

    def close(self) -> None:
        if getattr(self, "_closed", False):
            return
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
        super().close()

    def write(self, record: Row) -> None:
        raise WriteNotSupportedError("mdb", "Access MDB is read-only")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("mdb", "Access MDB is read-only")
