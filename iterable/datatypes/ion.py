from __future__ import annotations

import typing

try:
    import ion

    HAS_ION = True
except ImportError:
    HAS_ION = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class IonIterable(BaseFileIterable):
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
        if not HAS_ION:
            raise ImportError("Ion format support requires 'ion-python' package")
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            # Read Ion data
            data = self.fobj.read()
            self.iterator = iter(ion.loads(data, single_value=False))
        else:
            self.buffer = []

    @staticmethod
    def id() -> str:
        return "ion"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single Ion record"""
        value = next(self.iterator)
        self.pos += 1
        # Convert Ion value to dict
        if isinstance(value, dict):
            return value
        elif isinstance(value, list):
            # If it's a list, convert to dict with index
            return {str(i): v for i, v in enumerate(value)}
        else:
            return {"value": value}

    def write(self, record: Row) -> None:
        """Write single Ion record"""
        self.write_bulk(
            [
                record,
            ]
        )

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk Ion records"""
        for record in records:
            ion_data = ion.dumps(record)
            self.fobj.write(ion_data)
