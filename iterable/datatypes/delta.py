from __future__ import annotations

import os
import typing

try:
    import deltalake

    HAS_DELTALAKE = True
except ImportError:
    HAS_DELTALAKE = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteNotSupportedError
from ..types import Row


class DeltaIterable(BaseFileIterable):
    """Delta Lake table reader.

    Memory behavior: records are read batch by batch via
    ``DeltaTable.to_pyarrow_dataset().to_batches()``; the table is never
    fully materialized.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_DELTALAKE:
            raise ImportError("Delta Lake support requires 'deltalake' package")
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            # Delta Lake requires a path to the delta table directory
            if self.filename:
                self.delta_table = deltalake.DeltaTable(self.filename)
                # Lazy dataset: batches are pulled on demand, not materialized.
                self.dataset = self.delta_table.to_pyarrow_dataset()
                self.iterator = self.__iterator()
            else:
                raise ReadError(
                    "Delta Lake reading requires filename (path to delta table)",
                    filename=None,
                    error_code="RESOURCE_REQUIREMENT_NOT_MET",
                )
        else:
            raise WriteNotSupportedError("delta", "Delta Lake writing is not yet implemented")

    def __iterator(self):
        """Iterator for reading Delta table records batch by batch"""
        for batch in self.dataset.to_batches():
            yield from batch.to_pylist()

    @staticmethod
    def id() -> str:
        return "delta"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        """Records are read incrementally from dataset batches."""
        return True

    @staticmethod
    def has_tables() -> bool:
        """Indicates if this format supports multiple tables.

        Returns True only if using a catalog (not a single table directory).
        For single table directories, returns False.
        """
        # Delta Lake typically works with single table directories
        # Catalog support would require additional configuration
        # For now, return False as most usage is single table
        return False

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List available table names in the Delta Lake catalog or directory.

        Can be called as:
        - Instance method: `iterable.list_tables()` - uses instance's path
        - With filename: `iterable.list_tables(filename)` - opens catalog/directory temporarily

        Args:
            filename: Optional catalog path or table directory. If None, uses instance's filename.

        Returns:
            list[str] | None: List of table names if catalog-based, None if single table directory.
        """
        if not HAS_DELTALAKE:
            return None

        # Delta Lake typically uses single table directories
        # Catalog support (Unity Catalog, Hive Metastore) would require additional setup
        # For now, return None as most usage is single table directories
        target_path = filename if filename is not None else (self.filename if hasattr(self, "filename") else None)
        if target_path is None:
            return None

        # Check if path is a catalog or single table
        # This is a simplified check - actual catalog detection would require catalog configuration
        try:
            # If it's a directory with _delta_log, it's a single table
            if os.path.isdir(target_path) and os.path.exists(os.path.join(target_path, "_delta_log")):
                return None  # Single table directory

            # Could be a catalog path - but would need catalog configuration
            # For now, assume single table
            return None
        except Exception:
            return None

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if hasattr(self, "dataset") and self.dataset is not None:
            return self.dataset.count_rows()
        return 0

    def read(self, skip_empty: bool = True) -> dict:
        """Read single Delta record"""
        row = next(self.iterator)
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        """Write single Delta record - not supported"""
        raise WriteNotSupportedError("delta", "Delta Lake writing is not yet implemented")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk Delta records - not supported"""
        raise WriteNotSupportedError("delta", "Delta Lake writing is not yet implemented")
