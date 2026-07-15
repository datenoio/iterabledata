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
        filename: str | None = None,
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

    _UNPARSED = object()

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            content = self.fobj.read()
            self.items = []
            if content:
                data = self._UNPARSED
                try:
                    data = smile.loads(content)
                except Exception as e:
                    # Under on_error="raise" (default) this raises
                    # FormatParseError; "skip"/"warn" tolerate the failure
                    # and yield zero records explicitly.
                    self._handle_parse_failure("Failed to decode SMILE content", e)
                if data is not self._UNPARSED:
                    if isinstance(data, list):
                        self.items = data
                    elif isinstance(data, dict):
                        self.items = [data]
                    else:
                        self.items = [{"value": data}]

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
