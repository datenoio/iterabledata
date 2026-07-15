"""Apache Hudi table iterable (partial, table-path dependent).

Uses ``pyhudi`` or ``hudi`` when installed. Full table reads depend on the
installed library's API; write support is not implemented. Pass ``table_path``
(or ``filename``) pointing at a Hudi table directory.
"""

from __future__ import annotations

import logging
import os
import typing

try:
    from pyhudi import HudiCatalog

    HAS_PYHUDI = True
except ImportError:
    try:
        import hudi  # noqa: F401

        HAS_HUDI = True
        HAS_PYHUDI = False
    except ImportError:
        HAS_HUDI = False
        HAS_PYHUDI = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteNotSupportedError
from ..types import Row


class HudiIterable(BaseFileIterable):
    """Apache Hudi table reader.

    Memory behavior: the whole table is materialized in memory on open;
    this format does not stream records incrementally. This is a residual
    full-load path: the available Python bindings (``pyhudi``) only expose
    ``to_pandas()`` and offer no record-batch iteration API.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        table_path: str | None = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_PYHUDI and not HAS_HUDI:
            raise ImportError("Apache Hudi support requires 'pyhudi' or 'hudi' package")
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, noopen=True, options=options)
        self.table_path = table_path
        if "table_path" in options:
            self.table_path = options["table_path"]
        if stream is not None:
            raise ReadError(
                "Hudi requires table_path, not a stream",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        if self.table_path is None and self.filename is None:
            raise ReadError(
                "Hudi requires table_path parameter",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        if self.table_path is None:
            self.table_path = self.filename
        self.table = None
        self.iterator = None
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0

        if self.mode == "r":
            if HAS_PYHUDI:
                catalog = HudiCatalog()
                self.table = catalog.load_table(self.table_path)
                df = self.table.to_pandas()
                self.iterator = iter(df.to_dict("records"))
            else:
                # The 'hudi' package exposes a different API that is not yet
                # supported; failing is better than silently reading empty.
                raise ImportError(
                    "Reading Hudi tables via the 'hudi' package is not implemented. "
                    "Install 'pyhudi' instead: pip install pyhudi"
                )
        else:
            raise WriteNotSupportedError("hudi", "Hudi writing is not yet implemented")

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns table totals"""
        if self.table is None:
            return 0
        if HAS_PYHUDI:
            df = self.table.to_pandas()
            return len(df)
        return 0

    @staticmethod
    def id() -> str:
        return "hudi"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        """Memory behavior: the whole file/table is materialized on open."""
        return False

    @staticmethod
    def has_tables() -> bool:
        """Indicates if this format supports multiple tables."""
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List available table names in the Hudi catalog or directory.

        Can be called as:
        - Instance method: `iterable.list_tables()` - reuses catalog if available
        - With filename: `iterable.list_tables(filename)` - connects to catalog/directory temporarily

        Args:
            filename: Optional catalog path or directory. If None, uses instance's table_path.

        Returns:
            list[str]: List of table names, or empty list if no tables. Returns None if single table path.

        Raises:
            ImportError: If no Hudi library is installed.
            ReadError: If the target path does not exist or the catalog cannot be read.
        """
        if not HAS_PYHUDI and not HAS_HUDI:
            raise ImportError("Apache Hudi support requires 'pyhudi' or 'hudi' package")

        target_path = filename if filename is not None else (self.table_path if hasattr(self, "table_path") else None)
        if target_path is None:
            return None

        if not os.path.exists(target_path):
            raise ReadError(
                f"Hudi table or catalog path does not exist: '{target_path}'",
                filename=str(target_path),
                error_code="PATH_NOT_FOUND",
            )

        if not HAS_PYHUDI:
            # The 'hudi' package does not expose catalog listing.
            return None

        catalog = HudiCatalog()
        if not hasattr(catalog, "list_tables"):
            # Catalog cannot enumerate tables; treat the path as a single table.
            return None
        try:
            tables = catalog.list_tables(target_path)
            return [str(t) for t in tables] if tables else []
        except Exception as e:
            # Listing fails for single-table paths; that interpretation is
            # part of this method's contract (None == single table), but the
            # underlying cause is logged so genuine catalog errors are visible.
            logging.debug(f"Hudi catalog listing failed for '{target_path}' (treating as single table): {e}")
            return None

    def read(self, skip_empty: bool = True) -> dict:
        """Read single Hudi record"""
        try:
            row = next(self.iterator)
            self.pos += 1
            return row
        except (StopIteration, EOFError, ValueError):
            raise StopIteration from None

    def write(self, record: Row) -> None:
        """Write single Hudi record"""
        raise WriteNotSupportedError("hudi", "Hudi writing is not yet implemented")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk Hudi records"""
        raise WriteNotSupportedError("hudi", "Hudi writing is not yet implemented")
