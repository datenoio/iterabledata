from __future__ import annotations

import os
import typing

try:
    import pyiceberg  # noqa: F401
    from pyiceberg.catalog import load_catalog
    from pyiceberg.table import Table  # noqa: F401

    HAS_PYICEBERG = True
except ImportError:
    HAS_PYICEBERG = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteNotSupportedError
from ..types import Row


class IcebergIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        catalog_name: str | None = None,
        table_name: str | None = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_PYICEBERG:
            raise ImportError("Apache Iceberg support requires 'pyiceberg' package")
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, noopen=True, options=options)
        self.catalog_name = catalog_name
        self.table_name = table_name
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
        if self.catalog_name is None or self.table_name is None:
            raise ReadError(
                "Iceberg requires catalog_name and table_name parameters",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        self.table = None
        self.scan_result = None
        self.iterator = None
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0

        # Load catalog and table
        # For file-based catalog, filename might be the catalog properties file
        if self.filename and os.path.exists(self.filename):
            # Assume filename is a catalog properties file
            catalog = load_catalog(self.catalog_name, **{"properties": self.filename})
        else:
            # Use default catalog configuration
            catalog = load_catalog(self.catalog_name)

        self.table = catalog.load_table(self.table_name)

        if self.mode == "r":
            # Scan table
            self.scan_result = self.table.scan()
            # Convert to iterator of dicts
            self.iterator = iter(self.scan_result.to_arrow().to_pylist())
        else:
            raise WriteNotSupportedError("iceberg", "Iceberg writing is not yet implemented")

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns table totals"""
        if self.table is None:
            return 0
        # Count rows in table
        scan_result = self.table.scan()
        return len(scan_result.to_arrow())

    @staticmethod
    def id() -> str:
        return "iceberg"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_tables() -> bool:
        """Indicates if this format supports multiple tables."""
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List available table names in the Iceberg catalog.

        Can be called as:
        - Instance method: `iterable.list_tables()` - reuses catalog connection if available
        - With filename: `iterable.list_tables(filename)` - connects to catalog temporarily

        Args:
            filename: Optional catalog properties file. If None, uses instance's catalog configuration.

        Returns:
            list[str]: List of table names in the catalog, or empty list if no tables.
        """
        if not HAS_PYICEBERG:
            return None

        # Determine catalog configuration
        catalog_name = self.catalog_name if hasattr(self, "catalog_name") else None
        if catalog_name is None:
            return None

        # Load catalog
        try:
            if filename and os.path.exists(filename):
                catalog = load_catalog(catalog_name, **{"properties": filename})
            elif hasattr(self, "filename") and self.filename and os.path.exists(self.filename):
                catalog = load_catalog(catalog_name, **{"properties": self.filename})
            else:
                catalog = load_catalog(catalog_name)

            # List tables in catalog
            # Note: Catalog API may vary, this is a common pattern
            if hasattr(catalog, "list_tables"):
                tables = catalog.list_tables()
                return [str(t) for t in tables] if tables else []
            elif hasattr(catalog, "list_namespaces"):
                # Some catalogs require listing namespaces first
                namespaces = catalog.list_namespaces()
                all_tables = []
                for ns in namespaces:
                    try:
                        tables = catalog.list_tables(ns)
                        all_tables.extend([str(t) for t in tables])
                    except Exception:
                        continue
                return sorted(all_tables) if all_tables else []
            else:
                # Fallback: try to access tables attribute or method
                return []
        except Exception:
            return None

    def read(self, skip_empty: bool = True) -> dict:
        """Read single Iceberg record"""
        try:
            row = next(self.iterator)
            self.pos += 1
            return row
        except (StopIteration, EOFError, ValueError):
            raise StopIteration from None

    def write(self, record: Row) -> None:
        """Write single Iceberg record"""
        raise WriteNotSupportedError("iceberg", "Iceberg writing is not yet implemented")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk Iceberg records"""
        raise WriteNotSupportedError("iceberg", "Iceberg writing is not yet implemented")
