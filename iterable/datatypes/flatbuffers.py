from __future__ import annotations

import typing

try:
    import flatbuffers

    HAS_FLATBUFFERS = True
except ImportError:
    HAS_FLATBUFFERS = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import WriteNotSupportedError
from ..types import Row


class FlatBuffersIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        schema_file: str = None,
        root_type: str = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_FLATBUFFERS:
            raise ImportError("FlatBuffers support requires 'flatbuffers' package")
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.schema_file = schema_file
        self.root_type = root_type
        if "schema_file" in options:
            self.schema_file = options["schema_file"]
        if "root_type" in options:
            self.root_type = options["root_type"]
        # Note: FlatBuffers requires generated Python code from schema
        # This is a simplified implementation
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
                    # FlatBuffers files can contain multiple messages
                    # This is a simplified implementation
                    # In practice, you'd need the generated Python classes from the schema
                    messages = []
                    # For now, we'll assume a single message or need schema info
                    # This would need to be customized based on actual schema
                    messages.append({"data": "FlatBuffers reading requires schema-specific implementation"})
                    self.iterator = iter(messages)
            except Exception:
                self.iterator = iter([])
        else:
            # Write mode
            self.builder = flatbuffers.Builder(1024)

    @staticmethod
    def id() -> str:
        return "flatbuffers"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single FlatBuffers record"""
        try:
            row = next(self.iterator)
            self.pos += 1
            return row
        except (StopIteration, EOFError, ValueError):
            raise StopIteration from None

    def write(self, record: Row) -> None:
        """Write single FlatBuffers record"""
        # FlatBuffers writing requires schema-specific implementation
        # This is a placeholder
        raise WriteNotSupportedError("flatbuffers", "FlatBuffers writing requires schema-specific generated code")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk FlatBuffers records"""
        for record in records:
            self.write(record)
