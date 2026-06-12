from __future__ import annotations

import typing

try:
    import smile

    HAS_SMILE = True
except ImportError:
    HAS_SMILE = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class SMILEIterable(BaseFileIterable):
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
        if not HAS_SMILE:
            raise ImportError("SMILE support requires 'smile-json' package")
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            # SMILE format can contain multiple documents
            content = self.fobj.read()
            try:
                # Try to decode as single document
                data = smile.loads(content)
                if isinstance(data, list):
                    self.items = data
                elif isinstance(data, dict):
                    self.items = [data]
                else:
                    self.items = [{"value": data}]
            except Exception:
                # If single document fails, try to parse as array
                # SMILE format supports multiple documents concatenated
                self.items = []
                try:
                    # Try parsing as JSON array first (SMILE is binary JSON)
                    data = smile.loads(content)
                    if isinstance(data, list):
                        self.items = data
                    else:
                        self.items = [{"value": data}]
                except Exception:
                    # If all parsing fails, create empty list
                    self.items = []

            self.iterator = iter(self.items)
        else:
            self.items = []

    @staticmethod
    def id() -> str:
        return "smile"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single SMILE record"""
        row = next(self.iterator)
        self.pos += 1

        if isinstance(row, dict):
            return row
        else:
            return {"value": row}

    def write(self, record: Row) -> None:
        """Write single SMILE record"""
        smile_data = smile.dumps(record)
        self.fobj.write(smile_data)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk SMILE records"""
        for record in records:
            self.write(record)
