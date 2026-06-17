from __future__ import annotations

import typing

try:
    import pyreadstat

    HAS_PYREADSTAT = True
except ImportError:
    HAS_PYREADSTAT = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteNotSupportedError
from ..types import Row


class StataIterable(BaseFileIterable):
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
        if not HAS_PYREADSTAT:
            raise ImportError("Stata file support requires 'pyreadstat' package")
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            # pyreadstat requires file path, not file object
            if self.filename:
                df, meta = pyreadstat.read_dta(self.filename)
                self.data = df.to_dict("records")
                self.iterator = iter(self.data)
            else:
                raise ReadError(
                    "Stata file reading requires filename, not stream",
                    filename=None,
                    error_code="RESOURCE_REQUIREMENT_NOT_MET",
                )
        else:
            raise WriteNotSupportedError("stata", "Stata file writing is not yet implemented")

    @staticmethod
    def id() -> str:
        return "dta"

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
            df, meta = pyreadstat.read_dta(self.filename)
            return len(df)
        elif hasattr(self, "data"):
            return len(self.data)
        return 0

    def read(self, skip_empty: bool = True) -> dict:
        """Read single Stata record"""
        row = next(self.iterator)
        self.pos += 1
        # Convert numpy types to Python types
        return {k: (v.item() if hasattr(v, "item") else v) for k, v in row.items()}

    def write(self, record: Row) -> None:
        """Write single Stata record - not supported"""
        raise WriteNotSupportedError("stata", "Stata file writing is not yet implemented")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk Stata records - not supported"""
        raise WriteNotSupportedError("stata", "Stata file writing is not yet implemented")
