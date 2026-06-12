from __future__ import annotations

import typing

try:
    import ubjson

    HAS_UBJSON = True
except ImportError:
    HAS_UBJSON = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class UBJSONIterable(BaseFileIterable):
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
        if not HAS_UBJSON:
            raise ImportError("UBJSON support requires 'py-ubjson' package")
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            try:
                if hasattr(self.fobj, "seek"):
                    self.fobj.seek(0)
                # Read all data
                data = self.fobj.read()
                if len(data) == 0:
                    self.iterator = iter([])
                else:
                    # Decode UBJSON data
                    self.data = ubjson.loadb(data)
                    if isinstance(self.data, list):
                        self.iterator = iter(self.data)
                    else:
                        # Single object, wrap in list
                        self.iterator = iter([self.data])
            except Exception:
                self.iterator = iter([])
        else:
            # Write mode - no initialization needed
            pass

    @staticmethod
    def id() -> str:
        return "ubjson"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single UBJSON record"""
        try:
            row = next(self.iterator)
            self.pos += 1
            return row
        except (StopIteration, EOFError, ValueError):
            raise StopIteration from None

    def write(self, record: Row) -> None:
        """Write single UBJSON record"""
        encoded = ubjson.dumpb(record)
        self.fobj.write(encoded)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk UBJSON records"""
        for record in records:
            self.write(record)
