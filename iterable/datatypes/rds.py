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


class RDSIterable(BaseFileIterable):
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
            raise ImportError("RDS file support requires 'pyreadr' package")
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
                # RDS contains a single object, typically stored under None key
                df = result.get(None) or list(result.values())[0] if result else None
                if df is not None:
                    self.data = df.to_dict("records")
                    self.iterator = iter(self.data)
                else:
                    self.data = []
                    self.iterator = iter(self.data)
            else:
                raise ReadError(
                    "RDS file reading requires filename, not stream",
                    filename=None,
                    error_code="RESOURCE_REQUIREMENT_NOT_MET",
                )
        else:
            raise WriteNotSupportedError("rds", "RDS file writing is not yet implemented")

    @staticmethod
    def id() -> str:
        return "rds"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if self.filename:
            result = pyreadr.read_r(self.filename)
            df = result.get(None) or list(result.values())[0] if result else None
            if df is not None:
                return len(df)
            return 0
        elif hasattr(self, "data"):
            return len(self.data)
        return 0

    def read(self, skip_empty: bool = True) -> dict:
        """Read single RDS record"""
        row = next(self.iterator)
        self.pos += 1
        # Convert numpy types to Python types
        return {k: (v.item() if hasattr(v, "item") else v) for k, v in row.items()}

    def write(self, record: Row) -> None:
        """Write single RDS record - not supported"""
        raise WriteNotSupportedError("rds", "RDS file writing is not yet implemented")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk RDS records - not supported"""
        raise WriteNotSupportedError("rds", "RDS file writing is not yet implemented")
