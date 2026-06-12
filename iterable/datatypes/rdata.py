from __future__ import annotations

import typing

try:
    import pyreadr

    HAS_PYREADR = True
except ImportError:
    HAS_PYREADR = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteNotSupportedError
from ..types import Row


class RDataIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_PYREADR:
            raise ImportError("RData file support requires 'pyreadr' package")
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            # pyreadr requires file path, not file object
            if self.filename:
                result = pyreadr.read_r(self.filename)
                # RData can contain multiple objects, iterate through all
                self.data = []
                for obj_name, df in result.items():
                    if df is not None:
                        # Convert each dataframe to dict records
                        records = df.to_dict("records")
                        # Add object name as metadata if multiple objects
                        if len(result) > 1:
                            for record in records:
                                record["_r_object_name"] = obj_name
                        self.data.extend(records)
                self.iterator = iter(self.data)
            else:
                raise ReadError(
                    "RData file reading requires filename, not stream",
                    filename=None,
                    error_code="RESOURCE_REQUIREMENT_NOT_MET",
                )
        else:
            raise WriteNotSupportedError("rdata", "RData file writing is not yet implemented")

    @staticmethod
    def id() -> str:
        return "rdata"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_tables() -> bool:
        """Indicates if this format supports multiple tables/objects."""
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List available R object names in the RData file.

        Args:
            filename: Optional filename. If None, uses instance's filename.

        Returns:
            list[str]: List of R object names, or empty list if no objects.
        """
        target_filename = filename if filename is not None else self.filename
        if target_filename is None:
            return None

        # If data is already loaded, reuse it
        if filename is None and hasattr(self, "data") and self.data is not None:
            # We need to reload to get object names, but we can check if we have the result
            # Actually, we need to read the file again to get object names
            # pyreadr.read_r returns a dict with object names as keys
            result = pyreadr.read_r(target_filename)
            return list(result.keys())

        # Read file to get object names
        result = pyreadr.read_r(target_filename)
        return list(result.keys())

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if self.filename:
            result = pyreadr.read_r(self.filename)
            total = 0
            for df in result.values():
                if df is not None:
                    total += len(df)
            return total
        elif hasattr(self, "data"):
            return len(self.data)
        return 0

    def read(self, skip_empty: bool = True) -> dict:
        """Read single RData record"""
        row = next(self.iterator)
        self.pos += 1
        # Convert numpy types to Python types
        return {k: (v.item() if hasattr(v, "item") else v) for k, v in row.items()}

    def write(self, record: Row) -> None:
        """Write single RData record - not supported"""
        raise WriteNotSupportedError("rdata", "RData file writing is not yet implemented")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk RData records - not supported"""
        raise WriteNotSupportedError("rdata", "RData file writing is not yet implemented")
